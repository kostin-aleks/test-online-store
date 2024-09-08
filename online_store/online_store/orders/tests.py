"""
Test case to test models related to orders
"""

from datetime import date
from decimal import Decimal
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

from online_store.products.models import Product
from .models import Order
from online_store.general.test_utils import (
    get_test_user, ApiTestCase, create_test_manager_user,
    create_test_client_user)


class ApiOrdersTestCase(ApiTestCase):
    """
    Test case to test end-points of Mapster orders API
    """

    def setUp(self):
        self.client = APIClient()

        self.user_client = get_test_user(role='client')
        self.user_token, self.refresh_token = self.get_jwt_token(role='client')
        self.set_headers()

    def tearDown(self):
        self.client.logout()

    def order_data(self):
        ids = Product.objects.visible().values_list('id', flat=True)
        products = []
        for _ in range(3):
            id = random.choice(ids)
            products.append(Product.objects.get(pk=id))

        data = [{
            'product': product.id,
            'count': random.randint(1, 4)
        } for product in products]

        return {'items': data, 'price_currency': 'UAH'}

    def test_0020_orders(self):
        """
        end-point orders
        GET
        """
        self.user_manager = get_test_user(role='manager')
        self.user_token, self.refresh_token = self.get_jwt_token(role='manager')
        self.set_headers()

        response = self.client.get(reverse('orders'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        # pprint(data)
        self.assertTrue(data)
        self.assertTrue(len(data))
        result = data[0]
        self.assertTrue(result['id'])
        self.assertTrue(result['amount'])

    def test_0030_add_order(self):
        """
        end-point orders
        POST
        """
        data = self.order_data()
        response = self.client.post(reverse('orders'), data, format='json')

        response_data = json.loads(response.content)
        # pprint(response_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response_data['uuid'])
        self.assertTrue(response_data['id'])
        self.assertTrue('items' in response_data)
