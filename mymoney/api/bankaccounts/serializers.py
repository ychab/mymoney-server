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
        return ret


class BankAccountCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = BankAccount
        fields = ('id', 'label', 'balance_initial', 'currency')


class BankAccountDetailSerializer(serializers.ModelSerializer):
    balance_current = serializers.DecimalField(max_digits=10, decimal_places=2)
    balance_reconciled = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = BankAccount
        fields = ('id', 'label', 'balance', 'balance_initial',
                  'balance_current', 'balance_reconciled', 'currency')

    def to_representation(self, instance):
        instance.balance_current = BankTransaction.objects.get_current_balance(instance)
        instance.balance_reconciled = BankTransaction.objects.get_reconciled_balance(instance)
        return super(BankAccountDetailSerializer, self).to_representation(instance)
