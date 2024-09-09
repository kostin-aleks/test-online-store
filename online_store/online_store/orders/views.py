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

from online_store.general.error_messages import PRODUCT_NOT_FOUND, ORDER_NOT_FOUND
from online_store.general.utils import get_gender, atoi
from online_store.general.permissions import (
    IsManager, IsManagerOrReadOnly, IsClientUser)
from .models import Order, OrderItem, Payment
from .serializers import (
    OrderSerializer, OrderListItemSerializer,
    CreateOrderSerializer, OrderFullSerializer, PaymentSerializer,
    PaymentListItemSerializer, CreatePaymentSerializer,
)

logger = getLogger(__name__)


class OrderView(APIView, LimitOffsetPagination):
    permission_classes = [IsAuthenticated]
    serializer_type_class = {
        'get': OrderListItemSerializer,
        'post': CreateOrderSerializer,
    }

    def get_serializer_class(self):
        method = self.request.method.lower()
        serializer = self.serializer_type_class.get(method)
        if serializer:
            return serializer
        raise MethodNotAllowed(method=method)

    def get_queryset(self):
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
        user = request.user

        request_data = dict(request.data)

        context = {'user': user}
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
        return Order.objects.exclude(moderation_status='rejected')

    def get_serializer_class(self):
        return OrderFullSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        context['user'] = user
        return context

    def get(self, request, *args, **kwargs):
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

    def delete(self, request, *args, **kwargs):
        order_id = kwargs.get('pk')

        order = Order.objects.filter(pk=order_id).first()
        if order is None:
            return Response(ORDER_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        order.moderation_status = Order.Statuses.REJECTED
        order.save()

        return Response("Success")


class PaymentView(APIView, LimitOffsetPagination):
    permission_classes = [IsAuthenticated]
    serializer_type_class = {
        'get': PaymentListItemSerializer,
        'post': CreatePaymentSerializer,
    }

    def get_serializer_class(self):
        method = self.request.method.lower()
        serializer = self.serializer_type_class.get(method)
        if serializer:
            return serializer
        raise MethodNotAllowed(method=method)

    def get_queryset(self):
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

