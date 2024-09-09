"""
Manage command to create test categories
"""

from django.core.management.base import BaseCommand

from online_store.products.models import Category, SubCategory

CATEGORY_DATA = [
    {
        'name': 'Альпинизм',
        'slug': 'alpinism',
        'description': 'Снаряжение для альпинизма'
    },
    {
        'name': 'Туризм и отдых',
        'slug': 'turism-i-otdyh',
        'description': 'Снаряжение для активного отдыха на природе'
    },
    {
        'name': 'Водный спорт',
        'slug': 'vodny-sport',
        'description': 'Снаряжение для активного отдыха на воде'
    },
]

SUBCATEGORY_DATA = [
    {
        'name': 'Каски',
        'slug': 'kaski',
        'description': 'Защитные каски для альпинизма',
        'category': 'alpinism'
    },
    {
        'name': 'Карабины',
        'slug': 'karabiny',
        'description': 'Карабины для страховки',
        'category': 'alpinism'
    },
    {
        'name': 'Зажимы',
        'slug': 'zazhimy',
        'description': 'Зажим для подъёма по верёвке',
        'category': 'alpinism'
    },
    {
        'name': 'Палатки',
        'slug': 'palatki',
        'description': 'Палатки для туризма',
        'category': 'turism-i-otdyh'
    },
    {
        'name': 'Спальные мешки',
        'slug': 'spalnye-meshki',
        'description': 'Спальные мешки для туризма',
        'category': 'turism-i-otdyh'
    },
    {
        'name': 'Байдарки',
        'slug': 'bajdarki',
        'description': 'Байдарки',
        'category': 'vodny-sport'
    },
]


class Command(BaseCommand):
    """
    This manage command creates test categories
    """
    help = """Create test categories."""

    def handle(self, *args, **kwargs):
        """handler"""

        for item in CATEGORY_DATA:
            category = Category.objects.filter(slug=item['slug']).first()
            if category is None:
                category = Category.objects.create(
                    slug=item['slug'],
                    name=item['name'],
                    description=item['description']
                )
            else:
                category.name = item['name']
                category.description = item['description']
                category.save()

        for item in SUBCATEGORY_DATA:
            category = SubCategory.objects.filter(
                slug=item['slug'], category__slug=item['category']).first()
            if category is None:
                category = SubCategory.objects.create(
                    slug=item['slug'],
                    name=item['name'],
                    description=item['description'],
                    category=Category.objects.get(slug=item['category'])
                )
            else:
                category.name = item['name']
                category.description = item['description']
                category.save()
