"""
Manage command to create new test manager
"""
from faker import Faker

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model

from online_store.accounts.models import UserProfile


class Command(BaseCommand):
    """
    This manage command creates a test manager
    with related test data
    """
    help = """Create test manager data. You should point here the user mail"""
    user = None
    user_manager = None
    owner = None

    def add_arguments(self, parser):
        parser.add_argument(
            '-e', '--email', type=str, help='Email of test user')

    def handle(self, *args, **kwargs):
        fake = Faker()

        self.user_manager = None
        user = None
        email = kwargs['email']
        if email:
            user = get_user_model().objects.filter(
                email=email).first()

        if user is None:
            # get test user
            user = get_user_model().objects.filter(
                username=settings.API_TEST_MANAGER_USERNAME,
            ).first()

            if user is None:
                # create test user
                profile = fake.profile()
                first_name, last_name = profile['name'].split()
                email = fake.email()

                user = get_user_model().objects.create_user(
                    email=email,
                    username=settings.API_TEST_MANAGER_USERNAME,
                    password=settings.API_TEST_MANAGER_PASSWORD,
                    first_name=first_name,
                    last_name=last_name,
                )
                userprofile = UserProfile.objects.create(
                    user=user,
                    phone=fake.phone_number()[:15],
                    gender=0)
                user_profile.set_manager_permission()

        if user:
            if user.userprofile is None:
                userprofile = UserProfile.objects.create(
                    user=user,
                    phone=fake.phone_number()[:15],
                    gender=0)
                user_profile.set_manager_permission()

            self.user_manager = user.userprofile

        else:
            print('New test manager can not be created without user.')
