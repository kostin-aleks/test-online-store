import logging
from decimal import Decimal

from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from djmoney.models.fields import MoneyField
from djmoney.money import Money
from djmoney.models.validators import MinMoneyValidator

logger = logging.getLogger(__name__)

GENDERS = [
    (0, _('Male')),
    (1, _('Female'))]


class UserProfile(models.Model):
    """
    It stores User Profile data.
    Relation OneToOne to model User
    """
    user = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE, verbose_name=_("user"))
    phone = models.CharField(
        _("phone"),  # validators=[phoneNumberRegex],
        max_length=16, blank=True, null=True)
    gender = models.IntegerField(_("gender"), choices=GENDERS, null=True)

    def __str__(self):
        return self.user.username

    class Meta:
        db_table = 'accounts_user_profile'
        verbose_name = _("user profile")
        verbose_name_plural = _("user profiles")
        permissions = [
            ('manager', 'Store Manager'),
        ]

    def has_manager_permission(self):
        """
        Does the user have manager permission ?
        """
        return self.user.has_perm('accounts.manager')

    @classmethod
    def users_with_perm(cls, perm_name):
        return get_user_model().objects.filter(
            models.Q(is_superuser=True)
            | models.Q(user_permissions__codename=perm_name)
            | models.Q(groups__permissions__codename=perm_name)).distinct()

    def set_manager_permission(self):
        """
        set manager permission for user
        """
        content_type = ContentType.objects.get_for_model(UserProfile)
        permission = Permission.objects.get(
            codename='manager',
            content_type=content_type,
        )
        self.user.user_permissions.add(permission)

    def remove_manager_permission(self):
        """
        remove manager permission for user
        """
        content_type = ContentType.objects.get_for_model(UserProfile)
        permission = Permission.objects.get(
            codename='manager',
            content_type=content_type,
        )
        self.user.user_permissions.remove(permission)

    @receiver(post_save, sender=get_user_model())
    def update_user_profile(sender, instance, created, **kwargs):
        """
        A signal handler to create instance of User Profile
        when new User is created
        """
        if created:
            UserProfile.objects.create(user=instance)
        if instance.userprofile:
            instance.userprofile.save()

    def full_name(self):
        """
        user's full name
        """
        return f"{self.user.last_name} {self.user.first_name}"

    def create_token(self):
        refresh = RefreshToken.for_user(self.user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @property
    def balance_funds(self):
        """
        balance of funds
        """
        from online_store.orders.models import Payment

        addition = TopUpAccount.objects.filter(user=self.user).aggregate(Sum('amount'))
        paid = Payment.objects.filter(client=self.user).aggregate(Sum('amount'))
        balance = Decimal(addition['amount__sum'] or 0) - Decimal(paid['amount__sum'] or 0)
        return Money(balance, 'UAH')


class TopUpAccount(models.Model):
    user = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('user'), related_name='topupaccount')
    amount = MoneyField(
        _('price'), max_digits=14, decimal_places=2,
        default_currency='USD', validators=[MinMoneyValidator(0)],
        null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user.username}-{self.amount}"

    class Meta:
        verbose_name = _("Replenish Account")
        verbose_name_plural = _("Replenish Accounts")
        db_table = 'accounts_topup_account'
