"""
There are Admin Classes to present in admin interface objects related to products
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import SubCategory, Category, Product, Invoice, InvoiceItem, PriceAction


@admin.action(description=_("Approve moderation"))
def approve_moderation(modeladmin, request, queryset):
    """action approve_moderation"""
    queryset.update(moderation_status=Product.Statuses.APPROVED)


@admin.action(description=_("Reject moderation"))
def reject_moderation(modeladmin, request, queryset):
    """action reject_moderation"""
    queryset.update(moderation_status=Product.Statuses.CANCELLED)


class ProductAdmin(admin.ModelAdmin):
    """
    An ProductAdmin object encapsulates an instance of the Product
    """
    verbose_name = _('Product')
    verbose_name_plural = _('Products')
    list_display = (
        'id', 'name', 'moderation_status')
    search_fields = ('name', 'description')
    list_filter = ['subcategory', 'moderation_status']
    actions = [approve_moderation, reject_moderation]


admin.site.register(Product, ProductAdmin)


class CategoryAdmin(admin.ModelAdmin):
    """
    An CategoryAdmin object encapsulates an instance of the Category
    """
    verbose_name = _('Category')
    verbose_name_plural = _('Categories')
    list_display = (
        'id', 'slug', 'name')
    search_fields = ('name', 'slug')


admin.site.register(Category, CategoryAdmin)


class SubCategoryAdmin(admin.ModelAdmin):
    """
    An SubCategoryAdmin object encapsulates an instance of the SubCategory
    """
    verbose_name = _('Subcategory')
    verbose_name_plural = _('Subcategories')
    list_display = (
        'id', 'slug', 'name', 'category')
    search_fields = ('name', 'slug')
    list_filter = ['category']


admin.site.register(SubCategory, SubCategoryAdmin)


class InvoiceItemInline(admin.StackedInline):
    """
    Inline admin class to present Invoice Item
    """
    model = InvoiceItem
    verbose_name = 'Invoice Item'
    verbose_name_plural = 'Invoice Items'


class InvoiceAdmin(admin.ModelAdmin):
    """
    An InvoiceAdmin object encapsulates an instance of the Invoice
    with additional list of InvoiceItem
    """
    list_display = (
        'id', 'date', 'uuid')
    inlines = (InvoiceItemInline, )


admin.site.register(Invoice, InvoiceAdmin)


class PriceActionAdmin(admin.ModelAdmin):
    """
    An PriceActionAdmin object encapsulates an instance of the PriceAction
    """
    verbose_name = _('Price reduction action')
    verbose_name_plural = _('Price reduction actions')
    list_display = (
        'id', 'date', 'active', )  # 'discount'
    list_filter = ['active', 'date']
    ordering = ['-date', '-id']


admin.site.register(PriceAction, PriceActionAdmin)
