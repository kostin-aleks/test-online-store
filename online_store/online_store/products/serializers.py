from pprint import pprint
from slugify import slugify

from django.utils.translation import gettext as _

from rest_framework import serializers

from djmoney.money import Money

from .models import Category, SubCategory, Product


class SubCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SubCategory
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True)

    class Meta:
        model = Category
        fields = ['id', 'slug', 'name', 'description', 'subcategories']


class ProductListItemSerializer(serializers.ModelSerializer):
    subcategory = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'uuid', 'name', 'price', 'subcategory']

    @staticmethod
    def get_subcategory(obj):
        return obj.subcategory.slug if obj.subcategory else None


class ProductFullSerializer(serializers.ModelSerializer):
    subcategory = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    @staticmethod
    def get_subcategory(obj):
        return obj.subcategory.slug if obj.subcategory else None


class CreateProductSerializer(serializers.ModelSerializer):
    subcategory = serializers.CharField(required=False)
    price = serializers.FloatField()
    price_currency = serializers.CharField()

    class Meta:
        model = Product
        fields = [
            'subcategory', 'name', 'description', 'details',
            'features', 'technical_features', 'price', 'price_currency']

    def create(self, validated_data):

        instance = super(CreateProductSerializer, self).create(validated_data)

        return instance

    def update(self, instance, validated_data):

        product, created = Product.objects.update_or_create(
            id=instance.id, defaults=validated_data)

        return instance

    def validate(self, attrs):
        subcategory_slug = attrs.get('subcategory')
        if subcategory_slug:
            try:
                subcategory = SubCategory.objects.get(slug=subcategory_slug)
                attrs['subcategory'] = subcategory
            except SubCategory.DoesNotExist as e:
                raise serializers.ValidationError({'subcategory': _('Subcategory does not exist')})
        attrs['price'] = Money(attrs['price'], attrs['price_currency'])

        return attrs

