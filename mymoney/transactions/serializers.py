from django.template.defaultfilters import date as date_format

from rest_framework import serializers

from mymoney.core.utils import (
    get_default_account, localize_signed_amount,
    localize_signed_amount_currency,
)
from mymoney.tags.serializers import TagSerializer

from .models import AbstractTransaction, Transaction


class BaseTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = AbstractTransaction
        fields = (
            'id', 'label', 'date', 'amount', 'currency', 'status', 'reconciled',
            'payment_method', 'memo', 'tag',
        )

    def save(self, **kwargs):
        kwargs['account'] = get_default_account()
        super().save(**kwargs)


class TransactionSerializer(BaseTransactionSerializer):

    class Meta(BaseTransactionSerializer.Meta):
        model = Transaction
        fields = BaseTransactionSerializer.Meta.fields + ('scheduled',)


class TransactionDetailSerializer(TransactionSerializer):
    tag = TagSerializer()

    class Meta(TransactionSerializer.Meta):
        model = Transaction

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        ret['date_view'] = date_format(instance.date, 'SHORT_DATE_FORMAT')
        ret['amount_localized'] = localize_signed_amount(instance.amount)
        ret['amount_currency'] = localize_signed_amount_currency(
            instance.amount, instance.currency)
        ret['payment_method_display'] = instance.get_payment_method_display()
        ret['status_display'] = instance.get_status_display()

        return ret


class TransactionListSerializer(TransactionDetailSerializer):
    balance_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    balance_reconciled = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta(TransactionDetailSerializer.Meta):
        fields = TransactionDetailSerializer.Meta.fields + (
            'balance_total',
            'balance_reconciled',
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        fields = ('balance_total', 'balance_reconciled')
        for field in fields:
            attr = getattr(instance, field)
            key = field + '_view'
            if attr is not None:
                ret[key] = localize_signed_amount(attr)
            else:
                ret[key] = None

        return ret


class BaseTransactionMultipleSerializer(serializers.ModelSerializer):
    ids = serializers.PrimaryKeyRelatedField(
        queryset=Transaction.objects.all(),
        many=True,
        allow_empty=False,
    )

    class Meta:
        model = Transaction
        fields = ('ids',)


class TransactionPartialUpdateMutipleSerializer(BaseTransactionMultipleSerializer):
    class Meta(BaseTransactionMultipleSerializer.Meta):
        fields = ('ids', 'status', 'reconciled')


class TransactionDeleteMutipleSerializer(BaseTransactionMultipleSerializer):
    pass


class TransactionTeaserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transaction
        fields = ('id', 'label', 'date', 'amount', 'reconciled')
        read_only_fields = list(fields)
