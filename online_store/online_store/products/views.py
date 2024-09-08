import json
import jwt
from logging import getLogger
from decimal import Decimal
from pprint import pprint
import math
import requests
from time import time

from django.conf import settings
from django.db import transaction
from django.db.models import Min, Max
from django.utils.translation import gettext as _
#
from rest_framework.decorators import parser_classes, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    RetrieveUpdateAPIView, CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView)
from rest_framework.parsers import JSONParser
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework import status

from drf_spectacular.utils import extend_schema
from djmoney.money import Money

from online_store.general.error_messages import PRODUCT_NOT_FOUND
from online_store.general.utils import get_gender, atoi
from online_store.general.permissions import (
    IsManager, IsManagerOrReadOnly, IsClientUser)
from .models import Category, Product
from .filters import ProductFilters
from .serializers import (
    CategorySerializer, ProductListItemSerializer, CreateProductSerializer,
    ProductFullSerializer, InvoiceSerializer, InvoiceListItemSerializer,
    CreateInvoiceSerializer
)

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
        queryset = Product.objects.visible().select_related('subcategory')

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
                    items = [s.strip() for s in items.split(',') if s]
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
                subcategory__category__slug__in=categories)

        if subcategories:
            filtered_queryset = filtered_queryset.filter(
                subcategory__slug__in=subcategories)

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


class ProductByIdView(RetrieveUpdateDestroyAPIView):
    """
    get: Retrieve product by id
    put: Update product by id (available only to manager)
    delete: Delete product by id (available only to manager)
    """
    permission_classes = [IsManagerOrReadOnly]

    def get_queryset(self):
        return Product.objects.exclude(moderation_status='deleted')

    def get_serializer_class(self):
        return ProductFullSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        context['user'] = user
        return context

    def get(self, request, *args, **kwargs):
        user = self.request.user
        product = Product.objects.filter(
            pk=kwargs['pk']).exclude(
                moderation_status=Product.Statuses.DELETED).first()
        if product is None:
            return Response(PRODUCT_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        context = self.get_serializer_context()
        return Response(serializer_class(product, context=context).data)

    def delete(self, request, *args, **kwargs):
        product_id = kwargs.get('pk')

        product = Product.objects.filter(pk=product_id).first()
        if product is None:
            return Response(PRODUCT_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        product.moderation_status = Product.Statuses.DELETED
        product.save()

        # Изменить состояние заказов на "отменен гидом" для этого сервиса
        # cancel_orders_by_product(product)

        return Response("Success")

    @parser_classes([JSONParser])
    def put(self, request, pk, *args, **kwargs):
        """Custom update method: update product"""
        try:
            product = self.get_queryset().get(id=pk)
        except Product.DoesNotExist:
            return Response(PRODUCT_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        request_data = dict(request.data)

        context = self.get_serializer_context()

        product_srl = CreateProductSerializer(
            instance=product, data=request_data, partial=True, context=context)

        if not product_srl.is_valid():
            error_msg = _("Data is invalid, please check these fields:") + " "
            error_msg += ", ".join([_(f"{key}") for key in product_srl.errors.keys()])

            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        product = None
        with transaction.atomic():
            product = product_srl.save()
            context['product'] = product

        if product:
            return Response(
                ProductFullSerializer(product, context=context).data,
                status=status.HTTP_200_OK)


class InvoiceView(APIView, LimitOffsetPagination):
    permission_classes = [IsManager]
    serializer_type_class = {
        'get': InvoiceListItemSerializer,
        'post': CreateInvoiceSerializer,
    }

    def get_serializer_class(self):
        method = self.request.method.lower()
        serializer = self.serializer_type_class.get(method)
        if serializer:
            return serializer
        raise MethodNotAllowed(method=method)

    def get_queryset(self):
        queryset = Invoice.objects.all().order_by('-id')

        return queryset

    def get(self, request, *args, **kwargs):
        """
        GET list of incomes with filtration
        """
        user = request.user

        data = InvoiceListItemSerializer(
            filtered_queryset, context=context, many=True).data

        response = self.get_paginated_response(data)

        return response

    def post(self, request, *args, **kwargs):
        user = request.user

        request_data = dict(request.data)

        serializer = CreateInvoiceSerializer(data=request_data)
        if not serializer.is_valid():
            error_msg = _("Data is invalid, please check these fields:") + " "
            error_msg += ", ".join([_(f"{key}") for key in serializer.errors.keys()])
            serializer.validate(request_data)
            # print(error_msg)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        invoice = None
        with transaction.atomic():
            invoice = serializer.save()

        if invoice:
            return Response(
                InvoiceSerializer(invoice).data,
                status=status.HTTP_201_CREATED)
        else:
            raise ValidationError(
                _("Something went wrong"), status=status.HTTP_400_BAD_REQUEST)
