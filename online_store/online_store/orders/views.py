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
from .models import Order, OrderItem
from .serializers import (
    OrderSerializer, OrderListItemSerializer,
    CreateOrderSerializer
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
            print(error_msg)
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
