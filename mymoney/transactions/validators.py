from django.conf import settings
from django.utils.translation import ugettext as _

from rest_framework import exceptions

from .models import Transaction


class BankTransactionOwnerValidator(object):

    MAX = settings.MYMONEY.get('BULK_MAX', 50)

    def __init__(self, field):
        self.field = field
        self.user = None

    def set_context(self, serializer_field):
        self.user = serializer_field.context['request'].user

    def __call__(self, obj):
        value = obj.get(self.field, [])
        if not value:
            return

        if len(value) > self.MAX:
            raise exceptions.ValidationError(_(
                'The bulk limit of {max} is exceed.'.format(max=self.MAX)))

        banktransactions = (
            Transaction.objects
            .filter(
                pk__in=[v.pk for v in value],
                bankaccount__in=self.user.bankaccounts.all(),
            )
        )
        if set(bt.pk for bt in value) != set(bt.pk for bt in banktransactions):
            raise exceptions.ValidationError(_(
                'Some bank transaction are invalid.'))
