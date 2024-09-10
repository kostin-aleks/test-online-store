"""
products serializers
"""
from decimal import Decimal
# from pprint import pprint

from django.utils.translation import gettext as _

from rest_framework import serializers

from djmoney.money import Money

from .models import Category, SubCategory, Product, Invoice, InvoiceItem, PriceAction


class SubCategorySerializer(serializers.ModelSerializer):
    """
    Subcategory data
    """

    class Meta:
        model = SubCategory
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    """
    Category data
    """
    subcategories = SubCategorySerializer(many=True)

    class Meta:
        model = Category
        fields = ['id', 'slug', 'name', 'description', 'subcategories']


class ProductListItemSerializer(serializers.ModelSerializer):
    """
    Product data
    """
    subcategory = serializers.SerializerMethodField()
    available_quantity = serializers.IntegerField()
    actual_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'uuid', 'name', 'price', 'actual_price', 'subcategory',
            'available_quantity']

    @staticmethod
    def get_subcategory(obj):
        return obj.subcategory.slug if obj.subcategory else None

    def get_actual_price(self, obj):
        if self.context.get('action'):
            action = self.context['action']
            amount = obj.price.amount
            discount = action.discount
            new_price = amount * Decimal((100.0 - discount) / 100.0)
            return round(new_price, 2)
        return obj.price.amount


class ProductShortSerializer(serializers.ModelSerializer):
    """
    Product short data
    """
    subcategory = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'subcategory']

    @staticmethod
    def get_subcategory(obj):
        """getter for subcategory"""
        return obj.subcategory.slug if obj.subcategory else None


class ProductFullSerializer(serializers.ModelSerializer):
    """
    Product data
    """
    subcategory = serializers.SerializerMethodField()
    available_quantity = serializers.IntegerField()
    actual_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    @staticmethod
    def get_subcategory(obj):
        """getter for subcategory"""
        return obj.subcategory.slug if obj.subcategory else None

    def get_actual_price(self, obj):
        if self.context.get('action'):
            action = self.context['action']
            amount = obj.price.amount
            discount = action.discount
            new_price = amount * Decimal((100.0 - discount) / 100.0)
            return round(new_price, 2)
        return obj.price.amount


class CreateProductSerializer(serializers.ModelSerializer):
    """
    Product data to create new one
    """
    subcategory = serializers.CharField(required=False)
    price = serializers.FloatField()
    price_currency = serializers.CharField()

    class Meta:
        model = Product
        fields = [
            'subcategory', 'name', 'description', 'details',
            'features', 'technical_features', 'price', 'price_currency']

    def create(self, validated_data):
        """custom creating"""

        instance = super(CreateProductSerializer, self).create(validated_data)

        return instance

    def update(self, instance, validated_data):
        """custom updating"""

        product, created = Product.objects.update_or_create(
            id=instance.id, defaults=validated_data)

        return instance

    def validate(self, attrs):
        """custom validating"""
        subcategory_slug = attrs.get('subcategory')
        if subcategory_slug:
            try:
                subcategory = SubCategory.objects.get(slug=subcategory_slug)
                attrs['subcategory'] = subcategory
            except SubCategory.DoesNotExist:
                raise serializers.ValidationError({'subcategory': _('Subcategory does not exist')})
        attrs['price'] = Money(attrs['price'], attrs['price_currency'])

        return attrs


class InvoiceItemSerializer(serializers.Serializer):
    """
    Invoice Item
    """
    product = serializers.IntegerField()
    amount = serializers.IntegerField()
    price = serializers.FloatField(required=False)
    price_currency = serializers.CharField(required=False)


class CreateInvoiceSerializer(serializers.Serializer):
    """
    Data to create Invoice
    """
    date = serializers.DateField(input_formats=['%d-%m-%Y', 'iso-8601'])
    items = InvoiceItemSerializer(many=True)

    class Meta:
        fields = ['date', 'items']

    def create(self, validated_data):
        """custom creating"""

        instance = Invoice.objects.create(
            date=validated_data['date']
        )
        for item in validated_data['items']:

            InvoiceItem.objects.create(
                invoice=instance,
                product=Product.objects.get(pk=item['product']),
                amount=item['amount'],
                price=Money(item['price'], item['price_currency'])
            )

        return instance

    def validate(self, attrs):
        """custom validating"""
        for item in attrs['items']:
            product = Product.objects.filter(pk=item['product']).first()
            if product is None:
                raise serializers.ValidationError(
                    {'product': f"Product {item['product']} does not exist"})

        return attrs


class InvoiceItemOutSerializer(serializers.ModelSerializer):
    """
    Invoice
    """
    product = ProductShortSerializer()

    class Meta:
        model = InvoiceItem
        fields = ['id', 'product', 'amount', 'price']


class InvoiceSerializer(serializers.ModelSerializer):
    """
    Invoice
    """
    items = InvoiceItemOutSerializer(many=True)

    class Meta:
        model = Invoice
        fields = ['id', 'uuid', 'date', 'items']


class InvoiceListItemSerializer(serializers.ModelSerializer):
    """
    Invoice
    """

    class Meta:
        model = Invoice
        fields = '__all__'


class ProductPriceSerializer(serializers.Serializer):
    price = serializers.FloatField()


class CreateActionSerializer(serializers.Serializer):
    """
    Data to create Price Action
    """
    date = serializers.DateField(input_formats=['%d-%m-%Y', 'iso-8601'])
    discount = serializers.IntegerField()

    class Meta:
        fields = ['date', 'discount']

    def create(self, validated_data):
        """custom creating"""

        instance = PriceAction.objects.create(
            date=validated_data['date'],
            discount=validated_data['discount'],
            active=True,
        )

        return instance


class PriceActionItemOutSerializer(serializers.ModelSerializer):
    """
    Price Action
    """

    class Meta:
        model = PriceAction
        fields = ['id', 'date', 'discount', 'active']


class PriceActionSerializer(serializers.ModelSerializer):
    """
    Price Action
    """

    class Meta:
        model = PriceAction
        fields = ['id', 'date', 'discount', 'active']


class PriceActionListItemSerializer(serializers.ModelSerializer):
    """
    Price Action
    """

    class Meta:
        model = PriceAction
        fields = '__all__'


class DisableActionSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
