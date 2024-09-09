import logging
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.models import Sum
from django.db import models
from django.utils.translation import gettext_lazy as _

from djmoney.models.fields import MoneyField
from djmoney.money import Money
from djmoney.models.validators import MinMoneyValidator

logger = logging.getLogger(__name__)


class Category(models.Model):
    slug = models.SlugField(
        _("slug"), unique=True, null=True, blank=True, db_index=True)
    name = models.CharField(_("name"), max_length=128)
    description = models.CharField(
        _("description"), max_length=256, null=True, blank=True)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        db_table = 'products_category'

    def __str__(self) -> str:
        return self.name

    @property
    def subcategories(self):
        return self.sub_categories.all().order_by('slug')


class SubCategory(models.Model):
    slug = models.SlugField(
        _("slug"), unique=True, null=True, blank=True, db_index=True)
    name = models.CharField(_("name"), max_length=128)
    description = models.CharField(
        _("description"), max_length=256, null=True, blank=True)
    category = models.ForeignKey(
        Category, verbose_name=_("category"),
        related_name='sub_categories',
        on_delete=models.SET_NULL, null=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("Subcategory")
        verbose_name_plural = _("Subcategories")
        db_table = 'products_subcategory'


class CustomProductQuerySet(models.QuerySet):
    def visible(self):
        return self.filter(moderation_status="approved")


class ProductManager(models.Manager):
    def get_queryset(self):
        return CustomProductQuerySet(self.model, using=self._db)

    def visible(self):
        return self.get_queryset().visible()


class Product(models.Model):

    class Statuses(models.TextChoices):
        # waiting for admin approval
        PENDING = ("pending", _("Pending"))
        # admin approved profile
        APPROVED = ("approved", _("Approved"))
        # admin denied profile moderation
        CANCELLED = ("cancelled", _("Cancelled"))
        # owner deletes it
        DELETED = ("deleted", _("Deleted"))

    uuid = models.UUIDField(_("uuid"), default=uuid.uuid4, editable=False)
    subcategory = models.ForeignKey(
        SubCategory, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='products', verbose_name=_('subcategory'))
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True, null=True)
    details = models.JSONField(_('details'), blank=True, null=True)
    features = models.JSONField(_('features'), blank=True, null=True)
    technical_features = models.JSONField(_('technical features'), blank=True, null=True)
    price = MoneyField(
        _('price'), max_digits=14, decimal_places=2,
        default_currency='USD', validators=[MinMoneyValidator(0)],
        null=True, blank=True)

    moderation_status = models.CharField(
        _("moderation status"), choices=Statuses.choices,
        max_length=30, default=Statuses.PENDING, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    objects = ProductManager()

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        db_table = 'products_product'

    def __str__(self) -> str:
        return f'{self.name}'

    @property
    def available_quantity(self):
        """
        available quantity for this product
        """
        from online_store.orders.models import OrderItem

        purchased = InvoiceItem.objects.filter(product=self).aggregate(Sum('amount'))
        sold = OrderItem.objects.filter(product=self).aggregate(Sum('count'))
        balance = (purchased['amount__sum'] or 0) - (sold['count__sum'] or 0)
        return balance if balance >= 0 else 0


class Invoice(models.Model):
    uuid = models.UUIDField(_("uuid"), default=uuid.uuid4, editable=False)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self) -> str:
        return self.uuid

    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        db_table = 'products_invoice'


class InvoiceItem(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('product'))
    invoice = models.ForeignKey(
        Invoice, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='items', verbose_name=_('invoice'))
    amount = models.IntegerField()
    price = MoneyField(
        _('price'), max_digits=14, decimal_places=2,
        default_currency='USD', validators=[MinMoneyValidator(0)],
        null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.invoice.id}-{self.product.name}"

    class Meta:
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")
        db_table = 'products_invoice_item'

