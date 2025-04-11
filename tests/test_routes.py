######################################################################
# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from urllib.parse import quote_plus
from service import app
from service.common import status
from service.models import db, init_db, Product, Category
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        #
        # Uncomment this code once READ is implemented
        #

        # # Check that the location header was correct
        # response = self.client.get(location)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # new_product = response.get_json()
        # self.assertEqual(new_product["name"], test_product.name)
        # self.assertEqual(new_product["description"], test_product.description)
        # self.assertEqual(Decimal(new_product["price"]), test_product.price)
        # self.assertEqual(new_product["available"], test_product.available)
        # self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_read_a_product(self):
        """It should get the same info as the test product"""
        test_product = self._create_products(1)[0]

        response = self.client.get(BASE_URL + "/" + str(test_product.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_get_product_not_found(self):
        """It should return not found"""
        response = self.client.get(BASE_URL + "/" + "bad_id")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get(BASE_URL + "/" + "0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_a_product(self):
        """it should update the product then get the updated product"""

        test_product = self._create_products(1)[0]
        test_product.description = "new description"
        test_product.category = Category.UNKNOWN
        response = self.client.put(BASE_URL + "/" + str(test_product.id), json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(BASE_URL + "/" + str(test_product.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_update_product_not_found(self):
        """It should not update a product that does not exist"""
        product = ProductFactory()
        response = self.client.put(BASE_URL + "/" + "0", json=product.serialize())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_a_product(self):
        """it should create a product then delete it"""

        products = self._create_products(5)
        product_count = self.get_product_count()
        test_product = products[0]

        response = self.client.delete(BASE_URL + "/" + str(test_product.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(BASE_URL + "/" + str(test_product.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(product_count-1, self.get_product_count())


    def test_delete_product_not_found(self):
        """It should not delete a product that does not exist"""
        response = self.client.delete(BASE_URL + "/" + "0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_product_list(self):
        """it should create 5 products then read them"""

        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.get_json()), 0)

        products = self._create_products(5)        

        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.get_json()), 5)

    def test_query_by_name(self):
        """it should create 10 products then read get the ones that have the same name as the first"""
        products = self._create_products(10)        
        first_name = products[0].name
        count = 0
        for product in products:
            if product.name == first_name:
                count += 1

        response = self.client.get(BASE_URL, query_string=f"name={quote_plus(first_name)}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.get_json()), count)
        self.assertEqual(response.get_json()[0]['name'], first_name)

    def test_query_by_category(self):
        """it should create 10 products then read get the ones that have the same category as the first"""
        products = self._create_products(10)      
        first_category = products[0].category
        count = 0
        for product in products:
            if product.category == first_category:
                count += 1

        response = self.client.get(BASE_URL, query_string=f"category={quote_plus(str(first_category.value))}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.get_json()), count)
        first_product = Product().deserialize(response.get_json()[0])
        self.assertEqual(first_product.category, first_category)
    
    def test_query_by_availability(self):
        """it should create 10 products then read get the ones that have the same availability as the first"""
        products = self._create_products(10)        
        first_available = products[0].available
        count = 0
        for product in products:
            if product.available == first_available:
                count += 1

        response = self.client.get(BASE_URL, query_string=f"available={quote_plus(str(first_available))}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.get_json()), count)
        first_product = Product().deserialize(response.get_json()[0])
        self.assertEqual(first_product.available, first_available)
    
    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)
