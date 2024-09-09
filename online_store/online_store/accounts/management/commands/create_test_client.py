"""
Manage command to create new test Client
"""
from faker import Faker

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model

from online_store.accounts.models import UserProfile


class Command(BaseCommand):
    """
    This manage command creates a test client
    with related test data
    """
    help = """Create test client data. You should point here the user mail"""
    user = None
    user_client = None
    owner = None

    def add_arguments(self, parser):
        parser.add_argument(
            '-e', '--email', type=str, help='Email of test user')

    def handle(self, *args, **kwargs):
        fake = Faker()

        self.user_client = None
        user = None
        email = kwargs['email']
        if email:
            user = get_user_model().objects.filter(
                email=email).first()

        if user is None:
            # get test user
            user = get_user_model().objects.filter(
                username=settings.API_TEST_CLIENT_USERNAME,
            ).first()

            if user is None:
                # create test user
                profile = fake.profile()
                first_name, last_name = profile['name'].split()
                email = fake.email()

                user = get_user_model().objects.create_user(
                    email=email,
                    username=settings.API_TEST_CLIENT_USERNAME,
                    password=settings.API_TEST_CLIENT_PASSWORD,
                    first_name=first_name,
                    last_name=last_name,
                )
                UserProfile.objects.create(
                    user=user,
                    phone=fake.phone_number()[:15],
                    gender=0)

        if user:
            self.user_client = user.userprofile

        else:
            print('New test client can not be created without user with Client role.')
