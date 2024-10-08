"""
orders serializers
"""

from decimal import Decimal
# from pprint import pprint

from django.utils import timezone
# from django.utils.translation import gettext as _

from rest_framework import serializers

from djmoney.money import Money

from online_store.products.serializers import ProductShortSerializer
from online_store.products.models import Product
from .models import Order, OrderItem, Payment


class OrderItemSerializer(serializers.Serializer):
    """
    Order item
    """
    product = serializers.IntegerField()
    count = serializers.IntegerField()


class CreateOrderSerializer(serializers.Serializer):
    """
    Data for creating user order
    """
    price_currency = serializers.CharField()
    items = OrderItemSerializer(many=True)

    class Meta:
        fields = ['price_currency', 'items']

    def create(self, validated_data):
        """custom creating"""

        order = Order.objects.create(
            client=self.context['user'],
        )
        currency = validated_data['price_currency']
        amount = 0
        for item in validated_data['items']:
            product = Product.objects.get(pk=item['product'])
            count = item['count']

            action = self.context.get('action')
            product_amount = product.price.amount
            if action:
                discount = action.discount
                product_amount = amount * Decimal((100.0 - discount) / 100.0)
            product_amount = product_amount * Decimal(count)
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
        """custom validating"""
        for item in attrs['items']:
            product = Product.objects.filter(pk=item['product']).first()
            if product is None:
                raise serializers.ValidationError(
                    {'product': f"Product {item['product']} does not exist"})

        return attrs


class OrderItemOutSerializer(serializers.ModelSerializer):
    """Order Item"""
    product = ProductShortSerializer()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'amount']


class OrderSerializer(serializers.ModelSerializer):
    """Order"""
    items = OrderItemOutSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'uuid', 'created_at', 'items']


class OrderListItemSerializer(serializers.ModelSerializer):
    """Order"""

    class Meta:
        model = Order
        fields = '__all__'


class SoldProductListSerializer(serializers.ModelSerializer):
    """Sold Product"""
    client = serializers.SerializerMethodField()
    client_id = serializers.SerializerMethodField()
    order_id = serializers.SerializerMethodField()
    paid_at = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'amount', 'count', 'client', 'client_id',
            'order_id', 'paid_at']

    @staticmethod
    def get_client(obj):
        """
        get client user name
        """
        return obj.order.client.username

    @staticmethod
    def get_client_id(obj):
        """
        get client id
        """
        return obj.order.client.id

    @staticmethod
    def get_order_id(obj):
        """
        get order id
        """
        return obj.order.id

    @staticmethod
    def get_paid_at(obj):
        """
        get paid date
        """
        if obj.order.paid_at:
            return obj.order.paid_at.strftime('%Y-%m-%d')


class OrderFullSerializer(serializers.ModelSerializer):
    """Order full data"""
    items = OrderItemOutSerializer(many=True)

    class Meta:
        model = Order
        fields = '__all__'


class PaymentListItemSerializer(serializers.ModelSerializer):
    """Payment"""

    class Meta:
        model = Payment
        fields = '__all__'


class CreatePaymentSerializer(serializers.Serializer):
    """Data to create payment"""
    order = serializers.IntegerField()

    class Meta:
        fields = ['order']

    def create(self, validated_data):
        """custom creating"""
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
        """custom validating"""
        user = self.context['user']

        order = Order.objects.filter(pk=attrs['order']).first()
        if order is None:
            raise serializers.ValidationError(
                {'order': f"Order {order.id} does not exist"})
        if order.amount > user.userprofile.balance_funds:
            raise serializers.ValidationError(
                {'client': "The client has insufficient funds to pay for the order."})
        if order.moderation_status != Order.Statuses.NEW:
            raise serializers.ValidationError(
                {'order': "You can only pay for a new order"})

        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    """Payment"""

    class Meta:
        model = Payment
        fields = '__all__'


class FilterPaidProductsSerializer(serializers.Serializer):
    """
    Data for filtering list of paid products
    """
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    product = serializers.CharField(required=False)
    category = serializers.CharField(required=False)
    subcategory = serializers.CharField(required=False)
