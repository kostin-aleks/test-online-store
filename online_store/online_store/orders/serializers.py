from decimal import Decimal
from pprint import pprint
from slugify import slugify

from django.utils import timezone
from django.utils.translation import gettext as _

from rest_framework import serializers

from djmoney.money import Money

from online_store.products.serializers import ProductShortSerializer
from online_store.products.models import Product
from .models import Order, OrderItem, Payment


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


class OrderFullSerializer(serializers.ModelSerializer):
    items = OrderItemOutSerializer(many=True)

    class Meta:
        model = Order
        fields = '__all__'


class PaymentListItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = '__all__'


class CreatePaymentSerializer(serializers.Serializer):
    order = serializers.IntegerField()

    class Meta:
        fields = ['order']

    def create(self, validated_data):
        order = Order.objects.filter(pk=validated_data['order']).first()

        payment = Payment.objects.create(
            client=self.context['user'],
            order=order,
            amount=order.amount
        )
        order.moderation_status = Order.Statuses.PAID
        order.paid_at = timezone.now()
        order.save()

        return payment

    def validate(self, attrs):
        user = self.context['user']

        order = Order.objects.filter(pk=attrs['order']).first()
        if order is None:
            raise serializers.ValidationError(
                {'order': f"Order {item['order']} does not exist"})
        if order.amount > user.userprofile.balance_funds:
            raise serializers.ValidationError(
                {'client': "The client has insufficient funds to pay for the order."})
        if order.moderation_status != Order.Statuses.NEW:
            raise serializers.ValidationError(
                {'order': "You can only pay for a new order"})

        return attrs


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = '__all__'
