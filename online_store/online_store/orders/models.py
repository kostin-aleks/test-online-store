import logging
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import models
from django.utils.translation import gettext_lazy as _

from djmoney.models.fields import MoneyField
from djmoney.money import Money
from djmoney.models.validators import MinMoneyValidator

from online_store.products.models import Product

logger = logging.getLogger(__name__)


class Order(models.Model):

    class Statuses(models.TextChoices):
        NEW = ("new", _("New"))
        PAID = ("paid", _("Paid"))
        REJECTED = ("rejected", _("Rejected"))

    uuid = models.UUIDField(_("uuid"), default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE,
        related_name='orders', verbose_name=_('client'))
    amount = MoneyField(
        _('price'), max_digits=14, decimal_places=2,
        default_currency='USD', validators=[MinMoneyValidator(0)],
        null=True, blank=True)
    moderation_status = models.CharField(
        _("moderation status"), choices=Statuses.choices,
        max_length=30, default=Statuses.NEW, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        db_table = 'orders_order'

    def __str__(self) -> str:
        return f'{self.uuid}-{self.client.username}'


class OrderItem(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('product'))
    order = models.ForeignKey(
        Order, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='items', verbose_name=_('order'))
    count = models.IntegerField()
    amount = MoneyField(
        _('price'), max_digits=14, decimal_places=2,
        default_currency='USD', validators=[MinMoneyValidator(0)],
        null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.order.id}-{self.product.name}"

    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Orders Items")
        db_table = 'orders_order_item'


