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

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #
    def test_read_a_product(self):
        """ It should Create a product add it to the database then read it"""
        product = ProductFactory()
        logging.debug(f"product created: {product.serialize()}")
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        retrieved = Product.find(product.id)
        self.assertEqual(retrieved.name, product.name)
        self.assertEqual(retrieved.description, product.description)
        self.assertEqual(Decimal(retrieved.price), product.price)
        self.assertEqual(retrieved.available, product.available)
        self.assertEqual(retrieved.category, product.category)

    def test_update_a_product(self):
        """ It should Create a product then update it"""
        product = ProductFactory()
        logging.debug(f"product created: {product.serialize()}")
        product.id = None
        product.create()
        
        product.description = "New description"
        old_id = product.id
        product.update()
        self.assertEqual(product.description, "New description")
        self.assertEqual(product.id, old_id)

        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, product.id)
        self.assertEqual(products[0].description, product.description)
    
    def test_delete_a_product(self):
        """ It should Create a product then delete it then check it is not in the db"""
        product = ProductFactory()
        logging.debug(f"product created: {product.serialize()}")
        product.create()
        
        products = Product.all()
        self.assertEqual(len(products), 1)

        product.delete()

        products = Product.all()
        self.assertEqual(len(products), 0)
        
    def test_list_products(self):
        """ It should check the db is empty, create 5 products then check there are 5 products in the db"""
        products = Product.all()
        self.assertEqual(len(products), 0)

        for i in range(5):
            ProductFactory().create()
        
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_product_by_name(self):
        """ create 5 products then count the number of products with the same name as the first product then compare with results of find by name"""
        products = Product.all()
        self.assertEqual(len(products), 0)

        for i in range(5):
            ProductFactory().create()
        
        products = Product.all()
        self.assertEqual(len(products), 5)
        first = products[0]
        count = 0
        for product in products:
            if product.name == first.name:
                count += 1
        
        results = Product.find_by_name(first.name)
        self.assertEqual(results.count(), count)
        for result in results:
            self.assertEqual(result.name, first.name)

    def test_find_product_by_availability(self):
        """ create 10 products then count the number of products with the same availability as the first product then compare with results of find by availability"""
        products = Product.all()
        self.assertEqual(len(products), 0)

        for i in range(10):
            ProductFactory().create()
        
        products = Product.all()
        self.assertEqual(len(products), 10)
        avail = products[0].available
        count = 0
        for product in products:
            if product.available == avail:
                count += 1
        
        results = Product.find_by_availability(avail)
        self.assertEqual(results.count(), count)
        for result in results:
            self.assertEqual(result.available, avail)

    def test_find_product_by_category(self):
        """ create 10 products then count the number of products with the same category as the first product then compare with results of find by category"""
        products = Product.all()
        self.assertEqual(len(products), 0)

        for i in range(10):
            ProductFactory().create()
        
        products = Product.all()
        self.assertEqual(len(products), 10)
        category = products[0].category
        count = 0
        for product in products:
            if product.category == category:
                count += 1
        
        results = Product.find_by_category(category)
        self.assertEqual(results.count(), count)
        for result in results:
            self.assertEqual(result.category, category)
    
    def test_find_product_by_price(self):
        """ create 10 products then count the number of products with the same category as the first product then compare with results of find by category"""
        products = Product.all()
        self.assertEqual(len(products), 0)

        for i in range(10):
            ProductFactory().create()
        
        products = Product.all()
        self.assertEqual(len(products), 10)
        category = products[0].category
        count = 0
        for product in products:
            if product.category == category:
                count += 1
        
        results = Product.find_by_category(category)
        self.assertEqual(results.count(), count)
        for result in results:
            self.assertEqual(result.category, category)