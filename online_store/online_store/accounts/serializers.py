from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext as _

from rest_framework import serializers

from .models import UserProfile


class SignInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    class Meta:
        fields = ['username', 'password']

    def validate(self, attrs):
        username = attrs['username']
        # check if user with given username exists

        if not get_user_model().objects.filter(username=username).exists():
            raise ValidationError(_("User with that name does not exist"))

        user = authenticate(username=username, password=attrs['password'])

        if user:
            if user.is_active:
                attrs['user'] = user
            else:
                raise exceptions.ValidationError(_("User is deactivated"))
        else:
            raise exceptions.AuthenticationFailed(_("Wrong user name or password"))

        return attrs


class UserOutSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserOutSerializer()
    gender = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = '__all__'

    @staticmethod
    def get_gender(obj):
        if obj.gender is not None:
            return 'F' if obj.gender == 1 else 'M' if obj.gender == 0 else None


class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    gender = serializers.CharField(required=False)

    def validate(self, attrs):
        username = attrs['username']
        # check if user with given username exists

        if get_user_model().objects.filter(username=username).exists():
            raise ValidationError(_("User name is already used by another user"))

        user = authenticate(username=username, password=attrs['password'])

        return attrs
