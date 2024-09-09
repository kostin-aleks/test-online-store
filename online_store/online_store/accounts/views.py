import json
import jwt
from logging import getLogger
from pprint import pprint
import requests
from time import time

from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.translation import gettext as _
#
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveUpdateAPIView, CreateAPIView, ListAPIView
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework import status

from drf_spectacular.utils import extend_schema

from online_store.general.permissions import IsManager
from online_store.general.utils import get_gender
from .models import UserProfile
from .serializers import (
    SignInSerializer, UserProfileSerializer, SignUpSerializer,
    TopUpAccountSerializer, TopUpAccountItemSerializer)

logger = getLogger(__name__)


class SignInView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        methods=['post'],
        request=SignInSerializer,
        responses={201: UserProfileSerializer},
        operation_id='Sign In',
        description='POST auth/login')
    def post(self, request):
        serializer = SignInSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            serializer = self.get_serializer_class()
            return Response({
                'user': serializer(user.userprofile).data,
                'token': user.userprofile.create_token()})

    def get_serializer_class(self):
        return UserProfileSerializer


class SignUpView(CreateAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            #user = serializer.save()
            serdata = serializer.data
            user = get_user_model().objects.create_user(
                email=serdata['email'],
                username=serdata['username'],
                first_name=serdata.get('first_name'),
                last_name=serdata.get('last_name'),
                password=serdata['password'])

            user_profile, created = UserProfile.objects.get_or_create(
                user=user)
            user_profile.gender = get_gender(serdata.get('gender'))
            user_profile.phone = serdata.get('phone')
            user_profile.save()

            return Response(
                UserProfileSerializer(user_profile).data,
                status=status.HTTP_201_CREATED)
        else:
            raise ValidationError(serializer.errors)

    def get_serializer_class(self):
        return SignUpSerializer


class ProfileView(RetrieveUpdateAPIView):
    serializer_type_class = UserProfileSerializer

    def put(self, request, *args, **kwargs):
        user = request.user
        srl_class = self.get_profile_serializer()

        request_data = dict(request.data)

        serializer = srl_class(instance=user.userprofile, data=request_data, partial=True)
        if serializer.is_valid(raise_exception=True):
            user_profile = serializer.save()

            return Response(self.get_serializer_class()(user_profile).data)

    def get_object(self):
        return self.request.user.userprofile

    def get_serializer_class(self):
        return self.serializer_type_class

    @staticmethod
    def get_profile_serializer():
        return UserProfileSerializer


class TopUpAccountView(CreateAPIView):
    permission_classes = [IsManager]

    def post(self, request, *args, **kwargs):
        data = request.data

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            item = serializer.save()

            return Response(
                TopUpAccountItemSerializer(item).data,
                status=status.HTTP_201_CREATED)
        else:
            raise ValidationError(serializer.errors)

    def get_serializer_class(self):
        return TopUpAccountSerializer
