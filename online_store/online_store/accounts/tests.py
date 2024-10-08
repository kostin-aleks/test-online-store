"""
Test case to test models related to accounts
"""

import json
import unittest

from faker import Faker
# from pprint import pprint


from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from online_store.general.test_utils import (get_test_user, ApiTestCase)
from .models import UserProfile


class AccountTestCase(unittest.TestCase):
    """ unittest test case for accounts"""

    def setUp(self):
        """set up data"""
        self.user = get_user_model().objects.all().first()

    def test_00_user(self):
        """test user exists"""
        self.assertTrue(self.user)
        self.assertTrue(self.user.email)

    def test_01_users_count(self):
        """count of users"""
        users = get_user_model().objects.filter(is_active=True)
        self.assertTrue(users.count())

    def test_20_get_full_name(self):
        """get user's full name"""
        self.assertTrue(self.user.get_full_name())

    def test_30_profile(self):
        """user profile"""
        self.assertTrue(self.user.userprofile)

    def test_40_create_token(self):
        """create token"""
        token = self.user.userprofile.create_token()
        self.assertTrue(token)
        self.assertTrue(token.get('refresh'))
        self.assertTrue(token.get('access'))

    def test_50_has_manager_permission(self):
        """user has manager permission"""
        self.assertTrue(self.user.userprofile.has_manager_permission())

    def test_60_validate_role(self):
        """validate role"""
        managers = UserProfile.users_with_perm('manager')
        self.assertTrue(managers)

    def test_90_manager_profile(self):
        """manager profile"""
        profile = self.user.userprofile
        self.assertTrue(isinstance(profile, UserProfile))


class ApiAccountsTestCase(ApiTestCase):
    """
    Test case to test end-points of Mapster accounts API
    """

    def setUp(self):
        """set up data"""
        self.client = APIClient()

        self.user_client = get_test_user(role='client')
        self.user_token, self.refresh_token = self.get_jwt_token(role='client')
        self.set_headers()

    def tearDown(self):
        """tear down data"""
        self.client.logout()

    def test_0010_signup(self):
        """end-point POST SignUp"""
        fake = Faker()

        profile = fake.profile()
        first_name, last_name = profile['name'].split()
        username = profile['username']

        data = {
            "last_name": last_name,
            "first_name": first_name,
            'username': username,
            "email": fake.email(),
            'password': fake.password(),
            'phone': fake.phone_number()[:15],
            'gender': 'm'
        }
        response = self.client.post(reverse('signup-user'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)
        # pprint(content)
        self.assertTrue(data['user'])
        self.assertTrue(data['user']['username'])

    def test_0020_profile(self):
        """
        end-point profile
        GET, PUT
        """
        fake = Faker()

        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        # pprint(data)
        self.assertTrue(data['user'])
        self.assertTrue(data['user']['username'])

        data = {
            "phone": fake.phone_number()[:15],
        }
        response = self.client.put(reverse('profile'), data, format='json')

        data = json.loads(response.content)
        # pprint(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(data['user'])
        self.assertTrue(data['user']['username'])

    def test_0030_topup(self):
        """end-point POST top-up-account"""
        self.user_manager = get_test_user(role='manager')
        self.user_token, self.refresh_token = self.get_jwt_token(role='manager')
        self.set_headers()

        username = self.user_client.username

        data = {
            "username": username,
            "amount": 10000,
            'amount_currency': 'UAH',
        }

        response = self.client.post(reverse('top-up-account'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)
        # pprint(data)
        self.assertTrue(data['user'])
        self.assertTrue(data['amount'])
