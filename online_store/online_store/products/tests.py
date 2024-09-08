"""
Test case to test models related to accounts
"""

import json
from faker import Faker
from pprint import pprint
import random
import unittest

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from .models import Category, SubCategory, Product
from online_store.general.test_utils import (
    get_test_user, ApiTestCase, create_test_manager_user,
    create_test_client_user)


class ProductTestCase(unittest.TestCase):

    def setUp(self):
        self.category = Category.objects.first()
        self.subcategory = self.category.sub_categories.first()

    def tearDown(self):
        pass

    def test_00_category(self):
        self.assertTrue(self.category)
        self.assertTrue(self.category.slug)

    def test_10_categories_count(self):
        categories = Category.objects.all()
        self.assertTrue(categories.count())

    def test_20_subcategory(self):
        self.assertTrue(self.subcategory)
        self.assertTrue(self.subcategory.slug)

    def test_30_subcategories_count(self):
        subcategories = SubCategory.objects.all()
        self.assertTrue(subcategories.count())

    def test_40_product(self):
        self.product = Product.objects.first()
        self.assertTrue(self.product)

    def test_50_products_count(self):
        products = Product.objects.all()
        self.assertTrue(products.count())
        products = Product.objects.visible()
        self.assertTrue(products.count())


class ApiProductsTestCase(ApiTestCase):
    """
    Test case to test end-points of Mapster accounts API
    """

    def setUp(self):
        self.client = APIClient()

        self.user_client = get_test_user(role='client')
        self.user_token, self.refresh_token = self.get_jwt_token(role='client')
        self.set_headers()

    def tearDown(self):
        self.client.logout()

    def test_0010_categories(self):
        """
        end-point categories
        GET
        """
        response = self.client.get(reverse('categories'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        # pprint(data)
        self.assertTrue(data['count'])
        results = data['results']
        self.assertTrue(results)
        result = results[0]
        self.assertTrue(result['slug'])
        self.assertTrue(result['id'])

    def test_0020_products(self):
        """
        end-point products
        GET
        """
        params = "ordering=-price&min_price=1000&category=alpinism"
        response = self.client.get(reverse('products') + f"?{params}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        # pprint(data)
        self.assertTrue(data['count'])
        results = data['results']
        self.assertTrue(results)
        result = results[0]
        self.assertTrue(result['uuid'])
        self.assertTrue(result['id'])

    def test_0030_add_product(self):
        """
        end-point products
        POST
        """
        SUBCATEGORY = ['kaski', 'karabiny', 'zazhimy']
        NAME = {
            'kaski': 'Каска',
            'karabiny': 'Карабін',
            'zazhimy': 'Затиск',
        }
        BRAND = ['Salewa', 'First Ascent', 'Petzl', 'Black Diamond']
        COLOR = ['Сірий', 'Синій', 'Зелений']
        YEAR = [2014, 2015, 2019, 2022, 2024]
        DETAILS = ['Ергономічна рукоятка', 'Полегшена конструкція', 'компактна модель', 'Велика провушина для карабіна']

        fake = Faker()

        self.user_manager = get_test_user(role='manager')
        self.user_token, self.refresh_token = self.get_jwt_token(role='manager')
        self.set_headers()

        subcategory = random.choice(SUBCATEGORY)
        name = NAME[subcategory]
        brand = random.choice(BRAND)
        color = random.choice(COLOR)
        year = random.choice(YEAR)
        price = random.randint(200, 2000)
        weight = random.randint(300, 2000) / 1000

        data = {
            'name': f'Test {name} {brand} {color} {year}',
            'price': price,
            'description': fake.paragraph(nb_sentences=5),
            'price_currency': 'UAH',
            'subcategory': subcategory,
            'details': [random.choice(DETAILS), random.choice(DETAILS)],
            'features': {
                'Виробник': brand,
                'Колір': color},
            'technical_features': {
                'Вага': f'{weight:.1f} кг',
                'Колір': color},
        }
        response = self.client.post(reverse('products'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)
        # pprint(data)
        self.assertTrue(data['uuid'])
        self.assertTrue(data['price'])
        self.assertEqual(data['subcategory'], subcategory)
