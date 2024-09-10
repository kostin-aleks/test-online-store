"""
Functions and classes for tests
"""

import json
from faker import Faker
import random
import string
import unittest

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status

from online_store.accounts.models import UserProfile
from .utils import random_string_alphadigit


class ApiTestCase(unittest.TestCase):
    """
    Base class to test API end-cases
    """
    user_manager = None
    user_client = None
    user_admin = None

    def get_jwt_token(self, email=None, password=None, role='manager'):
        """login as user. get tokens"""
        if email is None and password is None:
            if role == 'manager':
                username = self.user_manager.username
                password = settings.API_TEST_MANAGER_PASSWORD
            if role == 'client':
                username = self.user_client.username
                password = settings.API_TEST_CLIENT_PASSWORD
            if role == 'admin':
                username = self.user_admin.username
                password = settings.API_TEST_ADMIN_PASSWORD

        response = self.client.post(
            reverse('signin'),
            {
                'username': username,
                'password': password,
            })
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        token = data.get('token')

        return token.get('access'), token.get('refresh')

    def set_headers(self, language='en'):
        """set autorization header"""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.user_token}',
            HTTP_ACCEPT_LANGUAGE=language,
        )


def get_test_category():
    """
    The test category
    """
#     category = GuideCategory.objects.filter(name=TEST_CATEGORY).first()
#     if category is None:
#         category = GuideCategory.objects.create(
#             name=TEST_CATEGORY)
#     return category
    return None


def get_test_user(role='manager'):
    """
    find first test user
    """
    if role == 'manager':
        username = settings.API_TEST_MANAGER_USERNAME
    if role == 'client':
        username = settings.API_TEST_CLIENT_USERNAME
    if role == 'admin':
        username = settings.API_TEST_ADMIN_USERNAME

    test_user = get_user_model().objects.filter(
        username=username).first()

    return test_user


def random_alphadigital(count):
    """
    string of random alphanumeric chars
    """
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=count))


def create_test_manager_user():
    """
    create test user with role manager
    """
    fake = Faker()

    password = fake.password()

    email = fake.email()
    email = f'{random_string_alphadigit(5)}.{email}'
    user_exists = get_user_model().objects.filter(
        email=email)
    cnt = 0
    while cnt < 100 and user_exists:
        email = fake.email()
        email = f'{random_string_alphadigit(5)}.{email}'
        user_exists = get_user_model().objects.filter(
            email=email)

    profile = fake.profile()
    first_name, last_name = profile['name'].split()
    username = profile['username']

    user = get_user_model().objects.create_user(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        password=password)

    user_profile = UserProfile.objects.create(
        user=user,
        gender=0,
        phone=fake.phone_number()[:15],
    )
    user_profile.set_manager_permission()

    return user, password


def create_test_client_user():
    """
    create test user with role client
    """
    fake = Faker()

    password = fake.password()

    email = f'{random_string_alphadigit(4)}.{fake.email()}'
    user_exists = get_user_model().objects.filter(
        email=email)
    cnt = 0
    while cnt < 100 and user_exists:
        email = f'{random_string_alphadigit(4)}.{fake.email()}'
        user_exists = get_user_model().objects.filter(
            email=email)

    profile = fake.profile()
    first_name, last_name = profile['name'].split()[:2]
    username = profile['username']

    user = get_user_model().objects.create_user(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        password=password)

    user_profile = UserProfile.objects.create(
        user=user,
        gender=0,
        phone=fake.phone_number()[:15],
    )

    return user, password
