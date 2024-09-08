from decimal import Decimal
from pprint import pprint
from slugify import slugify

from django.utils.translation import gettext as _

from rest_framework import serializers

from djmoney.money import Money

from online_store.products.serializers import ProductShortSerializer
from online_store.products.models import Product
from .models import Order, OrderItem


class OrderItemSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    count = serializers.IntegerField()


class CreateOrderSerializer(serializers.Serializer):
    price_currency = serializers.CharField()
    items = OrderItemSerializer(many=True)

    class Meta:
        fields = ['items']

    def create(self, validated_data):

        order = Order.objects.create(
            client=self.context['user'],
        )
        currency = validated_data['price_currency']
        amount = 0
        for item in validated_data['items']:
            product = Product.objects.get(pk=item['product'])
            count = item['count']
            product_amount = product.price.amount * Decimal(count)
            amount += product_amount

            OrderItem.objects.create(
                order=order,
                product=product,
                count=count,
                amount=Money(product_amount, currency)
            )

            order.amount = Money(amount, currency)
            order.save()
        return order

    def validate(self, attrs):
        for item in attrs['items']:
            product = Product.objects.filter(pk=item['product']).first()
            if product is None:
                raise serializers.ValidationError(
                    {'product': f"Product {item['product']} does not exist"})

        return attrs


class OrderItemOutSerializer(serializers.ModelSerializer):
    product = ProductShortSerializer()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'amount']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemOutSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'uuid', 'created_at', 'items']


class OrderListItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = '__all__'
