from rest_framework import serializers

from mymoney.api.banktransactions.models import BankTransaction
from mymoney.core.utils.currencies import localize_signed_amount_currency

from .models import BankAccount


class BankAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = BankAccount
        fields = ('id', 'label', 'balance', 'balance_initial', 'currency',
                  'owners')
        read_only_fields = ('owners',)

    def to_representation(self, instance):
        ret = super(BankAccountSerializer, self).to_representation(instance)
        ret['balance_view'] = localize_signed_amount_currency(
            instance.balance, instance.currency)
        ret['balance_initial_view'] = localize_signed_amount_currency(
            instance.balance_initial, instance.currency)
        return ret


class BankAccountCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = BankAccount
        fields = ('id', 'label', 'balance_initial', 'currency')


class BankAccountDetailSerializer(BankAccountSerializer):

    def to_representation(self, instance):
        ret = super(BankAccountDetailSerializer, self).to_representation(instance)
        ret['balance_current_view'] = localize_signed_amount_currency(
            BankTransaction.objects.get_current_balance(instance),
            instance.currency,
        )
        ret['balance_reconciled_view'] = localize_signed_amount_currency(
            BankTransaction.objects.get_reconciled_balance(instance),
            instance.currency,
        )
        return ret
