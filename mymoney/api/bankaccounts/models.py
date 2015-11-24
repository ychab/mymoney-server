from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from mymoney.core.utils.currencies import get_currencies


class BankAccountManager(models.Manager):

    def delete_orphans(self):
        """
        Delete bank account which have no more owners.
        """
        self.filter(owners__isnull=True).delete()


class BankAccount(models.Model):

    label = models.CharField(max_length=255, verbose_name=_('Label'))
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Balance'),
    )
    balance_initial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Initial balance'),
        help_text=_('Initial balance will automatically update the balance.'),
    )
    currency = models.CharField(
        max_length=3,
        choices=get_currencies(),
        verbose_name=_('Currency'),
    )
    owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        limit_choices_to={'is_staff': False, 'is_superuser': False},
        verbose_name=_('Owners'),
        related_name='bankaccounts',
        db_table='bankaccounts_owners',
    )

    objects = BankAccountManager()

    class Meta:
        db_table = 'bankaccounts'

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):

        # Init balance. Balance field is prior to initial balance.
        if self.pk is None:
            self.balance = self.balance_initial or self.balance
        # Otherwise update it with the new delta.
        else:
            original = BankAccount.objects.get(pk=self.pk)
            self.balance += (
                Decimal(self.balance_initial) -
                original.balance_initial
            )

        super(BankAccount, self).save(*args, **kwargs)
