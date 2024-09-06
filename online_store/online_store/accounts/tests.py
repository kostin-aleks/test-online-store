"""
Test case to test models related to accounts
"""

import json
from faker import Faker
from pprint import pprint
import unittest

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from .models import UserProfile
from online_store.general.test_utils import (
    get_test_user, ApiTestCase, create_test_manager_user,
    create_test_client_user)


class AccountTestCase(unittest.TestCase):

    def setUp(self):
        self.user = get_user_model().objects.all().first()

    def tearDown(self):
        pass

    def test_00_user(self):
        self.assertTrue(self.user)
        self.assertTrue(self.user.email)

    def test_01_users_count(self):
        users = get_user_model().objects.filter(is_active=True)
        self.assertTrue(users.count())

    def test_20_get_full_name(self):
        self.assertTrue(self.user.get_full_name())

    def test_30_profile(self):
        self.assertTrue(self.user.userprofile)

    def test_40_create_token(self):
        token = self.user.userprofile.create_token()
        self.assertTrue(token)
        self.assertTrue(token.get('refresh'))
        self.assertTrue(token.get('access'))

    def test_50_has_manager_permission(self):
        self.assertTrue(self.user.userprofile.has_manager_permission())

    def test_60_validate_role(self):
        managers = UserProfile.users_with_perm('manager')
        self.assertTrue(managers)

    def test_90_manager_profile(self):
        profile = self.user.userprofile
        self.assertTrue(isinstance(profile, UserProfile))


class ApiAccountsTestCase(ApiTestCase):
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
