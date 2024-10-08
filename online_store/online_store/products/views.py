"""
products views
"""
from decimal import Decimal
from logging import getLogger
# from pprint import pprint
import math

from django.db import transaction
from django.db.models import Min, Max
from django.utils.translation import gettext as _
#
from rest_framework.decorators import parser_classes
from rest_framework.exceptions import ValidationError, MethodNotAllowed
from rest_framework.generics import (
    ListAPIView, RetrieveUpdateDestroyAPIView)
from rest_framework.parsers import JSONParser
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework import status

from djmoney.money import Money

from online_store.general.error_messages import PRODUCT_NOT_FOUND, OBJECT_NOT_FOUND
from online_store.general.permissions import (
    IsManager, IsManagerOrReadOnly)
from .models import Category, Product, Invoice, PriceAction
from .filters import ProductFilters
from .serializers import (
    CategorySerializer, ProductListItemSerializer, CreateProductSerializer,
    ProductFullSerializer, InvoiceSerializer, InvoiceListItemSerializer,
    CreateInvoiceSerializer, ProductPriceSerializer,
    PriceActionSerializer, PriceActionListItemSerializer,
    CreateActionSerializer, DisableActionSerializer
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
    """
    GET and POST products
    """
    permission_classes = [IsManagerOrReadOnly]
    serializer_type_class = {
        'get': ProductListItemSerializer,
        'post': CreateProductSerializer,
    }

    def get_serializer_class(self):
        """get serializer class"""
        method = self.request.method.lower()
        serializer = self.serializer_type_class.get(method)
        if serializer:
            return serializer
        raise MethodNotAllowed(method=method)

    def get_queryset(self):
        """get queryset"""
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
            except Exception:
                non_default_ordering = True

        filtered_queryset = filtered_queryset.distinct()
        # paginate the filtered queryset
        filtered_queryset = self.paginate_queryset(
            filtered_queryset, request, view=self)

        # serialize the filtered queryset
        context = {'user': user, 'action': PriceAction.actual_action()}
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
        """create a new product"""
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
        """get queryset"""
        return Product.objects.exclude(moderation_status='deleted')

    def get_serializer_class(self):
        """get serializer class"""
        return ProductFullSerializer

    def get_serializer_context(self):
        """get serializer context"""
        context = super().get_serializer_context()
        user = self.request.user
        context['user'] = user
        context['action'] = PriceAction.actual_action()
        return context

    def get(self, request, *args, **kwargs):
        """GET one product by id"""

        product = Product.objects.filter(
            pk=kwargs['pk']).exclude(
                moderation_status=Product.Statuses.DELETED).first()
        if product is None:
            return Response(PRODUCT_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        context = self.get_serializer_context()
        return Response(serializer_class(product, context=context).data)

    def delete(self, request, *args, **kwargs):
        """delete one product by id (set status)"""
        from online_store.orders.service import cancel_orders_by_product
        product_id = kwargs.get('pk')

        product = Product.objects.filter(pk=product_id).first()
        if product is None:
            return Response(PRODUCT_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        product.moderation_status = Product.Statuses.DELETED
        product.save()

        cancel_orders_by_product(product)

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
    """
    GET and POST invoices
    """
    permission_classes = [IsManager]
    serializer_type_class = {
        'get': InvoiceListItemSerializer,
        'post': CreateInvoiceSerializer,
    }

    def get_serializer_class(self):
        """get serializer class"""
        method = self.request.method.lower()
        serializer = self.serializer_type_class.get(method)
        if serializer:
            return serializer
        raise MethodNotAllowed(method=method)

    def get_queryset(self):
        """get queryset"""
        queryset = Invoice.objects.all().order_by('-id')

        return queryset

    def get(self, request, *args, **kwargs):
        """
        GET list of incomes
        """
        context = {'user': request.user}
        data = InvoiceListItemSerializer(
            self.get_queryset(), context=context, many=True).data

        response = self.get_paginated_response(data)

        return response

    def post(self, request, *args, **kwargs):
        """create invoice"""
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


class ProductPriceView(APIView):
    """
    POST product price
    """
    permission_classes = [IsManager]
    http_method_names = ['post']

    def get_serializer_class(self):
        """get serializer class"""
        return ProductPriceSerializer

    def post(self, request, pk):
        """set product price"""
        request_data = dict(request.data)

        serializer = ProductPriceSerializer(data=request_data)
        if not serializer.is_valid():
            error_msg = _("Data is invalid, please check these fields:") + " "
            error_msg += ", ".join([_(f"{key}") for key in serializer.errors.keys()])
            serializer.validate(request_data)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        product = Product.objects.filter(pk=pk).first()
        if product is None:
            return Response(OBJECT_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        product.price = Money(Decimal(serializer.data['price']), 'UAH')
        product.save()

        return Response(
            ProductFullSerializer(product).data, status=status.HTTP_201_CREATED)


class PriceActionView(APIView, LimitOffsetPagination):
    """
    GET and POST price actions
    """
    permission_classes = [IsManager]
    serializer_type_class = {
        'get': PriceActionListItemSerializer,
        'post': CreateActionSerializer,
    }

    def get_serializer_class(self):
        """get serializer class"""
        method = self.request.method.lower()
        serializer = self.serializer_type_class.get(method)
        if serializer:
            return serializer
        raise MethodNotAllowed(method=method)

    def get_queryset(self):
        """get queryset"""
        queryset = PriceAction.objects.all().order_by('-id')

        return queryset

    def get(self, request, *args, **kwargs):
        """
        GET list of price actions
        """
        context = {'user': request.user}
        data = PriceActionListItemSerializer(
            self.get_queryset(), context=context, many=True).data

        #response = self.get_paginated_response(data)

        return Response(data)

    def post(self, request, *args, **kwargs):
        """create price action"""
        request_data = dict(request.data)

        serializer = CreateActionSerializer(data=request_data)
        if not serializer.is_valid():
            error_msg = _("Data is invalid, please check these fields:") + " "
            error_msg += ", ".join([_(f"{key}") for key in serializer.errors.keys()])
            serializer.validate(request_data)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            action = serializer.save()

        if action:
            return Response(
                PriceActionSerializer(action).data,
                status=status.HTTP_201_CREATED)
        else:
            raise ValidationError(
                _("Something went wrong"), status=status.HTTP_400_BAD_REQUEST)


class DisableActionView(APIView):
    """
    POST disable price action
    """
    permission_classes = [IsManager]
    http_method_names = ['post']

    def get_serializer_class(self):
        """get serializer class"""
        return DisableActionSerializer

    def post(self, request):
        """set product price"""
        request_data = dict(request.data)

        serializer = DisableActionSerializer(data=request_data)
        if not serializer.is_valid():
            error_msg = _("Data is invalid, please check these fields:") + " "
            error_msg += ", ".join([_(f"{key}") for key in serializer.errors.keys()])
            serializer.validate(request_data)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        action_id = serializer.data['pk']
        action = PriceAction.objects.filter(pk=action_id).first()
        if action is None:
            return Response(OBJECT_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        action.active = False
        action.save()

        return Response(
            PriceActionSerializer(action).data, status=status.HTTP_201_CREATED)

