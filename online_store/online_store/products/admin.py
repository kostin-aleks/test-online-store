"""
There are Admin Classes to present in admin interface objects related to products
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import SubCategory, Category, Product


@admin.action(description=_("Approve moderation"))
def approve_moderation(modeladmin, request, queryset):
    queryset.update(moderation_status=Product.Statuses.APPROVED)


@admin.action(description=_("Reject moderation"))
def reject_moderation(modeladmin, request, queryset):
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
