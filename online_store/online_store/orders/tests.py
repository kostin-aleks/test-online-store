"""
Test case to test models related to orders
"""

import json
# from pprint import pprint
import random

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from online_store.products.models import Product
from .models import Order
from online_store.general.test_utils import (get_test_user, ApiTestCase)


class ApiOrdersTestCase(ApiTestCase):
    """
    Test case to test end-points of Mapster orders API
    """

    def setUp(self):
        """set up data"""
        self.client = APIClient()

        self.user_client = get_test_user(role='client')
        self.user_token, self.refresh_token = self.get_jwt_token(role='client')
        self.set_headers()

    def tearDown(self):
        """tear down"""
        self.client.logout()

    def order_data(self):
        """populate order data"""
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

    def payment_data(self):
        """populate payment data"""
        order = Order.objects.filter(
            client=self.user_client, moderation_status='new').first()

        data = {'order': order.id}

        return data

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

    def test_0040_order_crud(self):
        """
        end-points for
        POST, DELETE, GET
        """
        self.user_manager = get_test_user(role='manager')
        self.user_token, self.refresh_token = self.get_jwt_token(role='manager')
        self.set_headers()

        data = self.order_data()

        response = self.client.post(
            reverse('orders'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = json.loads(response.content)
        # pprint(response_data)

        self.assertTrue(response_data['uuid'])
        self.assertTrue(response_data['id'])
        self.assertTrue('items' in response_data)

        order_id = response_data['id']

        response = self.client.get(reverse('get_order_by_id', args=[order_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        # pprint(response_data)
        self.assertTrue(response_data['uuid'])
        self.assertTrue(response_data['id'])
        self.assertTrue('items' in response_data)

        response = self.client.delete(
            reverse('get_order_by_id', args=[order_id]), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = Order.objects.filter(id=order_id).first()
        self.assertTrue(item)
        self.assertTrue(item.moderation_status == 'rejected')

    def test_0050_pay_order(self):
        """
        end-point payments
        POST
        """
        data = self.payment_data()
        response = self.client.post(reverse('payments'), data, format='json')

        response_data = json.loads(response.content)
        # pprint(response_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response_data['uuid'])
        self.assertTrue(response_data['id'])
        self.assertTrue(response_data['amount'])
