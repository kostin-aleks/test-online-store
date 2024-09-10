"""
Test case to test models related to products
"""

from datetime import date
from decimal import Decimal
import json
from faker import Faker
from pprint import pprint
import random
import unittest

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from .models import Category, SubCategory, Product, PriceAction
from online_store.general.test_utils import (get_test_user, ApiTestCase)


class ProductTestCase(unittest.TestCase):
    """
    unittest test case for products
    """

    def setUp(self):
        """set up"""
        self.category = Category.objects.first()
        self.subcategory = self.category.sub_categories.first()

    def tearDown(self):
        """tear down"""
        pass

    def test_00_category(self):
        """ category"""
        self.assertTrue(self.category)
        self.assertTrue(self.category.slug)

    def test_10_categories_count(self):
        """ count of categories """
        categories = Category.objects.all()
        self.assertTrue(categories.count())

    def test_20_subcategory(self):
        """ subcategory"""
        self.assertTrue(self.subcategory)
        self.assertTrue(self.subcategory.slug)

    def test_30_subcategories_count(self):
        """ count of subcategories """
        subcategories = SubCategory.objects.all()
        self.assertTrue(subcategories.count())

    def test_40_product(self):
        """product"""
        self.product = Product.objects.first()
        self.assertTrue(self.product)

    def test_50_products_count(self):
        """count of products"""
        products = Product.objects.all()
        self.assertTrue(products.count())
        products = Product.objects.visible()
        self.assertTrue(products.count())


class ApiProductsTestCase(ApiTestCase):
    """
    Test case to test end-points of Mapster products API
    """

    def setUp(self):
        """set up"""
        self.client = APIClient()

        self.user_client = get_test_user(role='client')
        self.user_token, self.refresh_token = self.get_jwt_token(role='client')
        self.set_headers()

    def tearDown(self):
        """tear down"""
        self.client.logout()

    def product_data(self):
        """populate data to create product"""
        SUBCATEGORY = ['kaski', 'karabiny', 'zazhimy']
        NAME = {
            'kaski': 'Каска',
            'karabiny': 'Карабін',
            'zazhimy': 'Затиск',
        }
        BRAND = ['Salewa', 'First Ascent', 'Petzl', 'Black Diamond']
        COLOR = ['Сірий', 'Синій', 'Зелений']
        YEAR = [2014, 2015, 2019, 2022, 2024]
        DETAILS = [
            'Ергономічна рукоятка', 'Полегшена конструкція', 'компактна модель',
            'Велика провушина для карабіна']

        fake = Faker()

        subcategory = random.choice(SUBCATEGORY)
        name = NAME[subcategory]
        brand = random.choice(BRAND)
        color = random.choice(COLOR)
        year = random.choice(YEAR)
        price = random.randint(200, 2000)
        weight = random.randint(300, 2000) / 1000

        return {
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
        # pprint(result)
        self.assertTrue(result['uuid'])
        self.assertTrue(result['id'])

    def test_0030_add_product(self):
        """
        end-point products
        POST
        """
        self.user_manager = get_test_user(role='manager')
        self.user_token, self.refresh_token = self.get_jwt_token(role='manager')
        self.set_headers()

        data = self.product_data()
        response = self.client.post(reverse('products'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = json.loads(response.content)
        # pprint(data)
        self.assertTrue(response_data['uuid'])
        self.assertTrue(response_data['price'])
        self.assertEqual(response_data['subcategory'], data['subcategory'])

    def test_0040_product_crud(self):
        """
        end-points for
        POST, DELETE
        PUT, GET
        """
        self.user_manager = get_test_user(role='manager')
        self.user_token, self.refresh_token = self.get_jwt_token(role='manager')
        self.set_headers()

        data = self.product_data()

        response = self.client.post(
            reverse('products'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = json.loads(response.content)

        self.assertTrue(response_data['uuid'])
        self.assertTrue(response_data['price'])
        self.assertEqual(response_data['subcategory'], data['subcategory'])

        product_id = response_data['id']

        data = self.product_data()
        response = self.client.put(
            reverse('get_product_by_id', args=[product_id]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse('get_product_by_id', args=[product_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        # pprint(response_data)
        self.assertTrue(response_data['uuid'])
        self.assertTrue(response_data['price'])
        self.assertEqual(response_data['subcategory'], data['subcategory'])

        response = self.client.delete(
            reverse('get_product_by_id', args=[product_id]), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = Product.objects.filter(id=product_id).first()
        self.assertTrue(item)
        self.assertTrue(item.moderation_status == 'deleted')

    def test_0050_invoice(self):
        """end-point POST invoice"""
        self.user_manager = get_test_user(role='manager')
        self.user_token, self.refresh_token = self.get_jwt_token(role='manager')
        self.set_headers()

        items = []
        for product in Product.objects.visible():
            items.append({
                'product': product.id,
                'amount': random.randint(10, 50),
                'price': product.price.amount * Decimal(0.8),
                'price_currency': 'UAH'
            })
        data = {
            "date": date.today().strftime('%Y-%m-%d'),
            "items": items
        }

        response = self.client.post(reverse('invoice'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)
        # pprint(data)
        self.assertTrue(data['uuid'])
        self.assertTrue(len(data['items']))

    def test_0060_set_product_price(self):
        """
        end-point product-price
        POST
        """
        self.user_manager = get_test_user(role='manager')
        self.user_token, self.refresh_token = self.get_jwt_token(role='manager')
        self.set_headers()

        product = Product.objects.visible().first()
        current_price = product.price.amount
        uuid = product.uuid

        data = {'price': current_price + 1}
        response = self.client.post(reverse('product-price', args=[product.id]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = json.loads(response.content)

        self.assertTrue(response_data['price'] > current_price)
        self.assertTrue(response_data['uuid'] == str(uuid))

    def test_0070_action(self):
        """end-point POST actions"""
        self.user_manager = get_test_user(role='manager')
        self.user_token, self.refresh_token = self.get_jwt_token(role='manager')
        self.set_headers()

        data = {
            "date": date.today().strftime('%Y-%m-%d'),
            "discount": 10
        }

        response = self.client.post(reverse('actions'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)
        # pprint(data)
        self.assertTrue(data['discount'])

    def test_0080_actions(self):
        """
        end-point actions
        GET
        """
        self.user_manager = get_test_user(role='manager')
        self.user_token, self.refresh_token = self.get_jwt_token(role='manager')
        self.set_headers()

        response = self.client.get(reverse('actions'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        # pprint(data)
        results = data
        self.assertTrue(results)
        result = results[0]
        self.assertTrue(result['discount'])
        self.assertTrue(result['id'])

    def test_0090_action(self):
        """end-point POST disable-price-action"""
        self.user_manager = get_test_user(role='manager')
        self.user_token, self.refresh_token = self.get_jwt_token(role='manager')
        self.set_headers()

        action = PriceAction.objects.first()
        data = {
            "pk": action.id,
        }

        response = self.client.post(
            reverse('disable-price-action'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)
        # pprint(data)
        self.assertTrue(data['discount'])
