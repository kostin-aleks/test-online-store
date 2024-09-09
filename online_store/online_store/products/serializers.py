# from pprint import pprint
from django.utils.translation import gettext as _

from rest_framework import serializers

from djmoney.money import Money

from .models import Category, SubCategory, Product, Invoice, InvoiceItem


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
    available_quantity = serializers.IntegerField()

    class Meta:
        model = Product
        fields = ['id', 'uuid', 'name', 'price', 'subcategory', 'available_quantity']

    @staticmethod
    def get_subcategory(obj):
        return obj.subcategory.slug if obj.subcategory else None


class ProductShortSerializer(serializers.ModelSerializer):
    subcategory = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'subcategory']

    @staticmethod
    def get_subcategory(obj):
        return obj.subcategory.slug if obj.subcategory else None


class ProductFullSerializer(serializers.ModelSerializer):
    subcategory = serializers.SerializerMethodField()
    available_quantity = serializers.IntegerField()

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
            except SubCategory.DoesNotExist:
                raise serializers.ValidationError({'subcategory': _('Subcategory does not exist')})
        attrs['price'] = Money(attrs['price'], attrs['price_currency'])

        return attrs


class InvoiceItemSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    amount = serializers.IntegerField()
    price = serializers.FloatField(required=False)
    price_currency = serializers.CharField(required=False)


class CreateInvoiceSerializer(serializers.Serializer):
    date = serializers.DateField(input_formats=['%d-%m-%Y', 'iso-8601'])
    items = InvoiceItemSerializer(many=True)

    class Meta:
        fields = ['date', 'items']

    def create(self, validated_data):

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
        for item in attrs['items']:
            product = Product.objects.filter(pk=item['product']).first()
            if product is None:
                raise serializers.ValidationError(
                    {'product': f"Product {item['product']} does not exist"})

        return attrs


class InvoiceItemOutSerializer(serializers.ModelSerializer):
    product = ProductShortSerializer()

    class Meta:
        model = InvoiceItem
        fields = ['id', 'product', 'amount', 'price']


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemOutSerializer(many=True)

    class Meta:
        model = Invoice
        fields = ['id', 'uuid', 'date', 'items']


class InvoiceListItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Invoice
        fields = '__all__'
