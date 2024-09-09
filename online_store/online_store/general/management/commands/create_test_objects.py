"""
Manage command to create test objects
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    This manage command creates a test objects
    with related test data
    """
    help = """Create test store objects."""

    def handle(self, *args, **kwargs):
        """handler"""
        call_command('create_test_client')
        call_command('create_test_manager')
        call_command('create_test_categories')
        call_command('create_test_products')

        print('New test objects are created.')
