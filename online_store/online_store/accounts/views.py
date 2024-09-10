"""
accounts views
"""

from logging import getLogger
# from pprint import pprint

from django.contrib.auth import get_user_model

from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveUpdateAPIView, CreateAPIView
from rest_framework.permissions import AllowAny
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


class SignInView(CreateAPIView):
    """
    sign in user
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """sign in new user"""
        serializer = SignInSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            serializer = self.get_serializer_class()
            return Response({
                'user': UserProfileSerializer(user.userprofile).data,
                'token': user.userprofile.create_token()})

        raise ValidationError(serializer.errors)

    def get_serializer_class(self):
        """get serializer class"""
        return SignInSerializer


class SignUpView(CreateAPIView):
    """
    sign up user
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """ sign up new user """
        data = request.data

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
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

        raise ValidationError(serializer.errors)

    def get_serializer_class(self):
        """get serializer class"""
        return SignUpSerializer


class ProfileView(RetrieveUpdateAPIView):
    """
    update user profile
    """
    serializer_type_class = UserProfileSerializer

    def put(self, request, *args, **kwargs):
        """ update user profile """
        user = request.user
        srl_class = self.get_profile_serializer()

        request_data = dict(request.data)

        serializer = srl_class(instance=user.userprofile, data=request_data, partial=True)
        if serializer.is_valid(raise_exception=True):
            user_profile = serializer.save()

            return Response(self.get_serializer_class()(user_profile).data)
        raise ValidationError(serializer.errors)

    def get_object(self):
        """get object"""
        return self.request.user.userprofile

    def get_serializer_class(self):
        """get serializer class"""
        return self.serializer_type_class

    @staticmethod
    def get_profile_serializer():
        """get profile serializer"""
        return UserProfileSerializer


class TopUpAccountView(CreateAPIView):
    """
    replenish client balance
    """
    permission_classes = [IsManager]

    def post(self, request, *args, **kwargs):
        """ replenish client balance """
        data = request.data

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            item = serializer.save()

            return Response(
                TopUpAccountItemSerializer(item).data,
                status=status.HTTP_201_CREATED)

        raise ValidationError(serializer.errors)

    def get_serializer_class(self):
        """get profile serializer"""
        return TopUpAccountSerializer
