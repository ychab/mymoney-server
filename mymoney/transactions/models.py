from datetime import date
from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from mymoney.accounts.models import Account
from mymoney.core.utils.dates import GRANULARITY_MONTH, get_date_ranges
from mymoney.tags.models import Tag


class TransactionManager(models.Manager):

    def get_current_balance(self, account):
        # Get futur balance instead for performance.
        futur_balance = (
            self
            .filter(account=account)
            .exclude(status=Transaction.STATUS_INACTIVE)
            .filter(date__gt=date.today())
            .aggregate(models.Sum('amount'))
        )['amount__sum'] or 0

        # Returns difference between total balance and future balance which is
        # finally the current balance.
        return Decimal(account.balance - futur_balance)

    def get_reconciled_balance(self, account):
        # Get non reconciled sum instead of sum of reconciled bank
        # transactions. By assuming that most of the bank transactions are
        # reconciled, it should be better for performance.
        total_not_reconciled = (
            self
            .filter(account=account)
            .filter(reconciled=False)
            .exclude(status=Transaction.STATUS_INACTIVE)
            .aggregate(models.Sum('amount'))
        )['amount__sum'] or 0

        return Decimal(account.balance - total_not_reconciled)

    def get_total_unscheduled_period(self, account, granularity=GRANULARITY_MONTH):
        """
        Returns the total sum for the current period of bank transactions not
        scheduled.
        """
        return (
            self
            .filter(
                account=account,
                date__range=get_date_ranges(timezone.now(), granularity),
                scheduled=False,
            )
            .exclude(status=Transaction.STATUS_INACTIVE)
            .aggregate(total=models.Sum('amount'))
        )['total'] or 0


class AbstractTransaction(models.Model):

    STATUS_ACTIVE = 'active'
    STATUS_IGNORED = 'ignored'
    STATUS_INACTIVE = 'inactive'
    STATUSES = (
        (STATUS_ACTIVE, _('Active')),
        (STATUS_IGNORED, _('Ignored')),
        (STATUS_INACTIVE, _('Inactive')),
    )

    PAYMENT_METHOD_CREDIT_CARD = 'credit_card'
    PAYMENT_METHOD_CASH = 'cash'
    PAYMENT_METHOD_TRANSFER = 'transfer'
    PAYMENT_METHOD_TRANSFER_INTERNAL = 'transfer_internal'
    PAYMENT_METHOD_CHECK = 'check'
    PAYMENT_METHODS = (
        (PAYMENT_METHOD_CREDIT_CARD, _('Credit card')),
        (PAYMENT_METHOD_CASH, _('Cash')),
        (PAYMENT_METHOD_TRANSFER, _('Transfer')),
        (PAYMENT_METHOD_TRANSFER_INTERNAL, _('Transfer internal')),
        (PAYMENT_METHOD_CHECK, _('Check')),
    )

    label = models.CharField(max_length=255, verbose_name=_('Label'))
    account = models.ForeignKey(
        Account,
        related_name='%(class)ss',
        on_delete=models.CASCADE,
    )
    date = models.DateField(default=date.today, verbose_name=_('Date'))
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Amount'),
    )
    currency = models.CharField(
        max_length=3,
        verbose_name=_('Currency'),
        editable=False,
    )
    status = models.CharField(
        max_length=32,
        choices=STATUSES,
        default=STATUS_ACTIVE,
        verbose_name=_('Status'),
        help_text=_("Depending on its value, determine whether it could alter "
                    "the bank account balance or being used by statistics.")
    )

    reconciled = models.BooleanField(
        default=False,
        verbose_name=_('Reconciled'),
        help_text=_("Whether the bank transaction has been applied on the "
                    "real bank account.")
    )
    payment_method = models.CharField(
        max_length=32,
        choices=PAYMENT_METHODS,
        default=PAYMENT_METHOD_CREDIT_CARD,
        verbose_name=_('Payment method'),
    )
    memo = models.TextField(blank=True, verbose_name=_('Memo'))
    tag = models.ForeignKey(
        Tag,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_('Tag'),
        related_name='%(class)ss',
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        self.currency = self.account.currency
        super().save(*args, **kwargs)


class Transaction(AbstractTransaction):

    scheduled = models.BooleanField(default=False, editable=False)

    objects = TransactionManager()

    class Meta:
        db_table = 'transactions'
        indexes = [
            models.Index(fields=['amount', 'date', 'reconciled']),
        ]
        get_latest_by = "date"

    def save(self, *args, **kwargs):

        if self.status == self.STATUS_INACTIVE:
            super().save(*args, **kwargs)
            return

        amount = Decimal(self.amount)
        if self.pk is not None:
            # Deduce previous value if updated.
            amount -= Decimal(Transaction.objects.get(pk=self.pk).amount)

        # Update bank account balance.
        try:
            with transaction.atomic():
                super().save(*args, **kwargs)

                self.account.balance = models.F('balance') + amount
                self.account.save(update_fields=['balance'])
        finally:
            # Reload it to replace F expression of instance attribute.
            self.account.refresh_from_db(fields=['balance'])

    def delete(self, *args, **kwargs):

        if self.status == self.STATUS_INACTIVE:
            super().delete(*args, **kwargs)
            return

        # Update bank account balance.
        try:
            with transaction.atomic():
                super().delete(*args, **kwargs)

                self.account.balance = (
                    models.F('balance') - Decimal(self.amount)
                )

                self.account.save()
        finally:
            self.account.refresh_from_db(fields=['balance'])
