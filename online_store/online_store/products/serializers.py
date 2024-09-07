# from pprint import pprint
from django.utils.translation import gettext as _

from rest_framework import serializers

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
    category = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'slug', 'name', 'price', 'category']

    @staticmethod
    def get_category(obj):
        return obj.category.slug


class CreateProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = [
            'slug', 'name', 'subtitle', 'description', 'details', 'features', 'price',
            'category', 'technical_features', ]


class CreateProductSerializer(serializers.ModelSerializer):
    category = serializers.IntegerField(required=False)
    price = serializers.FloatField()
    price_currency = serializers.CharField()

    class Meta:
        model = Product
        fields = [
            'category', 'name', 'subtitle', 'description', 'details',
            'features', 'technical_features', 'price']

    def create(self, validated_data):

        instance = super(CreateProductSerializer, self).create(validated_data)

        return instance

    def update(self, instance, validated_data):

        product, created = Product.objects.update_or_create(
            id=instance.id, defaults=validated_data)

        return instance

    def validate(self, attrs):

        category_id = attrs.get('category')
        if category_id:
            try:
                category = SubCategory.objects.get(pk=category_id)
                attrs['category'] = category
            except SubCategory.DoesNotExist as e:
                raise serializers.ValidationError({'category': _('Category does not exist')})
        attrs['price'] = Money(attrs['price'], attrs['price_currency'])

        return attrs

