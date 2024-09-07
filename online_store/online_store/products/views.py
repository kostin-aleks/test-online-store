import json
import jwt
from logging import getLogger
from decimal import Decimal
from pprint import pprint
import math
import requests
from time import time

from django.conf import settings
from django.db.models import Min, Max
from django.utils.translation import gettext as _
#
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveUpdateAPIView, CreateAPIView, ListAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework import status

from drf_spectacular.utils import extend_schema
from djmoney.money import Money

from online_store.general.utils import get_gender, atoi
from online_store.general.permissions import (
    IsManager, IsManagerOrReadOnly, IsClientUser)
from .models import Category, Product
from .filters import ProductFilters
from .serializers import (
    CategorySerializer, ProductListItemSerializer, CreateProductSerializer)

logger = getLogger(__name__)


class CategoriesView(ListAPIView):
    """List of categories"""
    permission_classes = [AllowAny]
    serializer_class = CategorySerializer
    queryset = Category.objects.all().order_by('id')
    paginate_by = 100
    paginate_by_param = 'page_size'
    max_paginate_by = 1000

    def get_queryset(self):
        """
        get list of categories
        """
        queryset = Category.objects.all().order_by('id')

        return queryset


class ProductView(APIView, LimitOffsetPagination):
    permission_classes = [IsManagerOrReadOnly]
    serializer_type_class = {
        'get': ProductListItemSerializer,
        'post': CreateProductSerializer,
    }

    def get_serializer_class(self):
        method = self.request.method.lower()
        serializer = self.serializer_type_class.get(method)
        if serializer:
            return serializer
        raise MethodNotAllowed(method=method)

    def get_queryset(self):
        queryset = Product.objects.visible().select_related('category')

        return queryset

    def get(self, request, *args, **kwargs):
        """
        GET list of products with filtration
        """
        def get_list(params, field_name):
            items = params.get(field_name)
            if items:
                if items == 'undefined':
                    items = []
                else:
                    items = [s.strip() for s in categories.split(',') if s]
            else:
                items = []
            return items

        user = request.user

        filters_from_request = request.query_params.dict()

        categories = get_list(request.query_params, 'category')
        subcategories = get_list(request.query_params, 'subcategory')

        query_params_without_price_filters = filters_from_request.copy()
        query_params_without_price_filters.pop('min_price', None)
        query_params_without_price_filters.pop('max_price', None)

        queryset = self.get_queryset()

        f_qs = ProductFilters(query_params_without_price_filters, queryset=queryset).qs

        # calculate min and max prices for the queryset, filtered without price filters
        min_price = max_price = None
        min_max_prices_data = f_qs.aggregate(
            min_price=Min('price'), max_price=Max('price'),
        )
        min_price = min_max_prices_data['min_price']
        max_price = min_max_prices_data['max_price']

        if min_price:
            min_price = math.ceil(min_price)
        if max_price:
            max_price = math.ceil(max_price)

        # filter queryset again, but with price filters
        filter_min_price = Decimal(atoi(filters_from_request.get('min_price'), 0))
        filter_max_price = Decimal(atoi(filters_from_request.get('max_price'), 1000000))

        filtered_queryset = ProductFilters(filters_from_request, queryset=queryset).qs
        if categories:
            filtered_queryset = filtered_queryset.filter(
                category__category__slug__in=categories)
        if subcategories:
            filtered_queryset = filtered_queryset.filter(
                category__slug__in=subcategories)

        # order the filtered queryset if ordering param was provided
        non_default_ordering = False
        order_by = request.query_params.get('ordering')
        # убрать неизвестный порядок сортировки
        if order_by not in ('price', '-price'):
            order_by = ''
        if order_by:
            try:
                filtered_queryset = filtered_queryset.order_by(order_by)
            except Exception as e:
                non_default_ordering = True

        filtered_queryset = filtered_queryset.distinct()
        # paginate the filtered queryset
        filtered_queryset = self.paginate_queryset(
            filtered_queryset, request, view=self)

        # serialize the filtered queryset
        context = {'user': user}
        data = ProductListItemSerializer(
            filtered_queryset, context=context, many=True).data

        if order_by and non_default_ordering:
            from operator import itemgetter
            descending = False  # whether to sort in descending order
            if order_by.startswith('-'):
                order_by = order_by[1:]
                descending = True
            data = sorted(data, key=itemgetter(order_by), reverse=descending)

        response = self.get_paginated_response(data)

        response.data['min_price'] = min_price
        response.data['max_price'] = max_price
        if isinstance(min_price, Money):
            response.data['min_price'] = min_price.amount
        if isinstance(max_price, Money):
            response.data['max_price'] = max_price.amount

        return response

    def post(self, request, *args, **kwargs):
        user = request.user

        request_data = dict(request.data)

        serializer = CreateProductSerializer(data=request_data)
        if not serializer.is_valid():
            error_msg = _("Data is invalid, please check these fields:") + " "
            error_msg += ", ".join([_(f"{key}") for key in serializer.errors.keys()])
            serializer.validate(request_data)
            # print(error_msg)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        product = None
        with transaction.atomic():
            product = serializer.save()

        if product:
            return Response(ProductFullSerializer(product).data, status=status.HTTP_201_CREATED)
        else:
            raise ValidationError(
                _("Something went wrong"), status=status.HTTP_400_BAD_REQUEST)
