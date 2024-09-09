from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext as _

from rest_framework import serializers
from rest_framework import exceptions

from djmoney.money import Money

from .models import UserProfile, TopUpAccount


class SignInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    class Meta:
        fields = ['username', 'password']

    def validate(self, attrs):
        username = attrs['username']
        # check if user with given username exists

        if not get_user_model().objects.filter(username=username).exists():
            raise exceptions.ValidationError(_("User with that name does not exist"))

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
    balance_funds = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'balance_funds']

    @staticmethod
    def get_balance_funds(obj):
        if obj.userprofile is not None:
            balance = obj.userprofile.balance_funds
            if balance is not None:
                return {
                    'amount': balance.amount,
                    'amount_currency': balance.currency.code}
            return None


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserOutSerializer()
    gender = serializers.SerializerMethodField()
    balance_funds = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = '__all__'

    @staticmethod
    def get_gender(obj):
        if obj.gender is not None:
            return 'F' if obj.gender == 1 else 'M' if obj.gender == 0 else None

    @staticmethod
    def get_balance_funds(obj):
        balance = obj.balance_funds
        if balance is not None:
            return {
                'amount': balance.amount,
                'amount_currency': balance.currency.code}
        return None


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
            raise exceptions.ValidationError(
                _("User name is already used by another user"))

        user = authenticate(username=username, password=attrs['password'])

        return attrs


class TopUpAccountSerializer(serializers.Serializer):
    username = serializers.CharField()
    amount = serializers.FloatField()
    amount_currency = serializers.CharField()

    def validate(self, attrs):
        username = attrs['username']
        # check if user with given username exists

        if not get_user_model().objects.filter(username=username).exists():
            raise exceptions.ValidationError(_("User not found"))

        return attrs

    def create(self, validated_data):
        user = get_user_model().objects.filter(
            username=validated_data['username']).first()

        instance = TopUpAccount.objects.create(
            user=user,
            amount=Money(validated_data['amount'], validated_data['amount_currency'])
        )

        return instance


class TopUpAccountItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = TopUpAccount
        fields = '__all__'
