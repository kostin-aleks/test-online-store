from django_filters import rest_framework as filters

from django.db.models.query import QuerySet

from .models import Product


class ProductFilters(filters.FilterSet):
    min_price = filters.NumberFilter(method='filter_min_price')
    max_price = filters.NumberFilter(method='filter_max_price')

    class Meta:
        model = Product
        fields = ['price']

    @staticmethod
    def filter_min_price(queryset: QuerySet, _, value: float | int) -> QuerySet:
        return queryset.filter(price__gte=value)

    @staticmethod
    def filter_max_price(queryset: QuerySet, _, value: float | int) -> QuerySet:
        return queryset.filter(price__lte=value)
