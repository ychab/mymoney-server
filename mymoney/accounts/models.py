from django.db import models
from django.utils.translation import ugettext_lazy as _

from mymoney.core.utils.currencies import get_currencies


class Account(models.Model):
    """
    For the moment, a bank account is a singleton.
    """
    label = models.CharField(max_length=255, verbose_name=_('Label'))
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Balance'),
    )
    currency = models.CharField(
        max_length=3,
        choices=get_currencies(),
        verbose_name=_('Currency'),
    )

    class Meta:
        db_table = 'accounts'

    def __str__(self):
        return self.label
