"""
orders views
"""

from logging import getLogger
# from pprint import pprint

from django.db import transaction
from django.utils.translation import gettext as _
#
from rest_framework.exceptions import ValidationError, MethodNotAllowed
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework import status

from online_store.general.error_messages import ORDER_NOT_FOUND, ACCESS_DENIED
from online_store.general.permissions import IsManager
from online_store.products.models import PriceAction
from .models import Order, OrderItem, Payment
from .serializers import (
    OrderSerializer, OrderListItemSerializer,
    CreateOrderSerializer, OrderFullSerializer, PaymentSerializer,
    PaymentListItemSerializer, CreatePaymentSerializer, SoldProductListSerializer,
    FilterPaidProductsSerializer,
)

logger = getLogger(__name__)


class OrderView(APIView, LimitOffsetPagination):
    """
    GET and POST Orders
    """
    permission_classes = [IsAuthenticated]
    serializer_type_class = {
        'get': OrderListItemSerializer,
        'post': CreateOrderSerializer,
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
        queryset = Order.objects.all().order_by('-id')

        return queryset

    def get(self, request, *args, **kwargs):
        """
        GET list of orders
        """
        user = request.user

        qs = self.get_queryset()
        if not user.userprofile.has_manager_permission():
            qs = qs.filter(client=user)

        context = {'user': user}
        data = OrderListItemSerializer(
            qs, context=context, many=True).data

        return Response(data)

    def post(self, request, *args, **kwargs):
        """ create order """
        user = request.user

        request_data = dict(request.data)

        context = {'user': user, 'action': PriceAction.actual_action()}
        serializer = CreateOrderSerializer(data=request_data, context=context)
        if not serializer.is_valid():
            error_msg = _("Data is invalid, please check these fields:") + " "
            error_msg += ", ".join([_(f"{key}") for key in serializer.errors.keys()])
            serializer.validate(request_data)
            # print(error_msg)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        order = None
        with transaction.atomic():
            order = serializer.save()

        if order:
            return Response(
                OrderSerializer(order).data,
                status=status.HTTP_201_CREATED)
        else:
            raise ValidationError(
                _("Something went wrong"), status=status.HTTP_400_BAD_REQUEST)


class OrderByIdView(RetrieveUpdateDestroyAPIView):
    """
    get: Retrieve order by id
    delete: Delete order by id (available only to manager)
    """
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'delete']

    def get_queryset(self):
        """get queryset"""
        return Order.objects.exclude(moderation_status='rejected')

    def get_serializer_class(self):
        """get serializer class"""
        return OrderFullSerializer

    def get_serializer_context(self):
        """get serializer content"""
        context = super().get_serializer_context()
        user = self.request.user
        context['user'] = user
        return context

    def get(self, request, *args, **kwargs):
        """get one order by id """
        user = self.request.user
        order = Order.objects.filter(
            pk=kwargs['pk']).exclude(
                moderation_status=Order.Statuses.REJECTED).first()
        if order is None:
            return Response(ORDER_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        if order.moderation_status != Order.Statuses.NEW:
            return Response(
                'Order can be rejected only if it is new one.',
                status=status.HTTP_403_FORBIDDEN)
        if order.client != user and not user.userprofile.has_manager_permission():
            return Response(ACCESS_DENIED, status=status.HTTP_403_FORBIDDEN)

        serializer_class = self.get_serializer_class()
        context = self.get_serializer_context()
        return Response(serializer_class(order, context=context).data)

    def delete(self, request, pk):
        """delete (set status) one order by id """
        order_id = pk
        user = request.user

        order = Order.objects.filter(pk=order_id).first()
        if order is None:
            return Response(ORDER_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        if not (order.client == user or user.userprofile.has_manager_permission()):
            return Response(ACCESS_DENIED, status=status.HTTP_403_FORBIDDEN)

        if order.client == user:
            order.moderation_status = Order.Statuses.REJECTED_BY_CLIENT
        else:
            if user.userprofile.has_manager_permission():
                order.moderation_status = Order.Statuses.REJECTED_BY_MANAGER

        order.save()

        return Response("Success")


class PaymentView(APIView, LimitOffsetPagination):
    """
    GET and POST payments
    """
    permission_classes = [IsAuthenticated]
    serializer_type_class = {
        'get': PaymentListItemSerializer,
        'post': CreatePaymentSerializer,
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
        queryset = Payment.objects.all().order_by('-id')

        return queryset

    def get(self, request, *args, **kwargs):
        """
        GET list of payments
        """
        user = request.user

        qs = self.get_queryset()
        if not user.userprofile.has_manager_permission():
            qs = qs.filter(client=user)

        context = {'user': user}
        data = PaymentListItemSerializer(
            qs, context=context, many=True).data

        return Response(data)

    def post(self, request, *args, **kwargs):
        """create payment"""
        user = request.user

        request_data = dict(request.data)

        context = {'user': user}
        serializer = CreatePaymentSerializer(data=request_data, context=context)
        if not serializer.is_valid():
            error_msg = _("Data is invalid, please check these fields:") + " "
            error_msg += ", ".join([_(f"{key}") for key in serializer.errors.keys()])
            serializer.validate(request_data)
            # print(error_msg)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        payment = None
        with transaction.atomic():
            payment = serializer.save()

        if payment:
            return Response(
                PaymentSerializer(payment).data,
                status=status.HTTP_201_CREATED)
        else:
            raise ValidationError(
                _("Something went wrong"), status=status.HTTP_400_BAD_REQUEST)


class SoldProductView(APIView, LimitOffsetPagination):
    """
    GET sold products
    """
    permission_classes = [IsManager]
    http_method_names = ['get']

    def get_serializer_class(self):
        """get serializer class"""
        return SoldProductListSerializer

    def get_queryset(self):
        """get queryset"""
        queryset = OrderItem.objects.filter(
            order__moderation_status=Order.Statuses.PAID
        ).filter(
            order__paid_at__isnull=False
        ).select_related('order', 'product')

        return queryset

    def get(self, request, *args, **kwargs):
        """
        GET list of sold products with filtration
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

        serializer = FilterPaidProductsSerializer(data=request.query_params.dict())
        if not serializer.is_valid():
            error_msg = _("Data is invalid, please check these fields:") + " "
            error_msg += ", ".join([_(f"{key}") for key in serializer.errors.keys()])
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        filters_from_request = serializer.data
        categories = get_list(filters_from_request, 'category')
        subcategories = get_list(filters_from_request, 'subcategory')
        products = get_list(filters_from_request, 'product')
        products = [int(item) for item in products]
        date_from = filters_from_request.get('date_from')
        date_to = filters_from_request.get('date_to')

        filtered_queryset = self.get_queryset()

        if categories:
            filtered_queryset = filtered_queryset.filter(
                product__subcategory__category__slug__in=categories)

        if subcategories:
            filtered_queryset = filtered_queryset.filter(
                product__subcategory__slug__in=subcategories)

        if products:
            filtered_queryset = filtered_queryset.filter(
                product__id__in=products)

        if date_from:
            filtered_queryset = filtered_queryset.filter(
                order__paid_at__date__gte=date_from)

        if date_to:
            filtered_queryset = filtered_queryset.filter(
                order__paid_at__date__lte=date_to)

        # order the filtered queryset if ordering param was provided
        non_default_ordering = False
        order_by = request.query_params.get('ordering')
        orderby = "order__paid_at"
        if order_by and order_by.startswith('-'):
            orderby = '-' + orderby

        filtered_queryset = filtered_queryset.distinct()
        # paginate the filtered queryset
        filtered_queryset = self.paginate_queryset(
            filtered_queryset, request, view=self)

        # serialize the filtered queryset
        context = {'user': user}
        data = SoldProductListSerializer(
            filtered_queryset, context=context, many=True).data

        response = self.get_paginated_response(data)

        return response
