import time

from django.template.defaultfilters import date as date_format

from rest_framework import serializers
from rest_framework.reverse import reverse

from mymoney.bankaccounts import CurrentBankAccountDefault
from mymoney.tags.serializers import \
    BankTransactionTagOutputSerializer
from mymoney.banktransactiontags import \
    BankTransactionTagOwnerValidator
from mymoney.core.utils.currencies import (
    localize_signed_amount, localize_signed_amount_currency,
)
from mymoney.core.validators import MinMaxValidator

from .models import AbstractTransaction, Transaction
from .validators import BankTransactionOwnerValidator


class BaseTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = AbstractTransaction
        fields = ('id', 'label', 'bankaccount', 'date', 'amount', 'currency',
                  'status', 'reconciled', 'payment_method', 'memo', 'tag')
        read_only_fields = ('bankaccount',)
        extra_kwargs = {
            'bankaccount': {'default': CurrentBankAccountDefault()},
            'tag': {'validators': [BankTransactionTagOwnerValidator()]}
        }


class TransactionSerializer(BaseTransactionSerializer):

    class Meta(BaseTransactionSerializer.Meta):
        model = Transaction
        fields = BaseTransactionSerializer.Meta.fields + ('scheduled',)


class BankTransactionDetailSerializer(serializers.ModelSerializer):
    tag = BankTransactionTagOutputSerializer()

    class Meta:
        model = Transaction
        fields = ('id', 'label', 'date', 'amount', 'status', 'reconciled',
                  'payment_method', 'memo', 'tag', 'scheduled')

    def to_representation(self, instance):
        ret = super(
            BankTransactionDetailSerializer, self).to_representation(instance)

        ret['date_view'] = date_format(instance.date, 'SHORT_DATE_FORMAT')
        ret['amount_localized'] = localize_signed_amount(instance.amount)
        ret['amount_currency'] = localize_signed_amount_currency(
            instance.amount, instance.currency)
        ret['payment_method_display'] = instance.get_payment_method_display()
        ret['status_display'] = instance.get_status_display()

        return ret


class BankTransactionDetailExtraSerializer(BankTransactionDetailSerializer):
    balance_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    balance_reconciled = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta(BankTransactionDetailSerializer.Meta):
        fields = (
            BankTransactionDetailSerializer.Meta.fields + (
                'balance_total', 'balance_reconciled')
        )

    def to_representation(self, instance):
        ret = super(
            BankTransactionDetailExtraSerializer, self).to_representation(instance)

        fields = ('balance_total', 'balance_reconciled')
        for field in fields:
            attr = getattr(instance, field)
            key = field + '_view'
            if attr is not None:
                ret[key] = localize_signed_amount(attr)
            else:
                ret[key] = None

        return ret


class BankTransactionTeaserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transaction
        fields = ('id', 'label', 'date', 'amount', 'reconciled')
        read_only_fields = list(fields)


class BaseTransactionMultipleSerializer(serializers.Serializer):
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


class BankTransactionEventInputSerializer(serializers.Serializer):
    date_from = TimestampMillisecond()
    date_to = TimestampMillisecond()

    class Meta:
        validators = [MinMaxValidator('date_from', 'date_to')]


class BankTransactionEventOutputSerializer(serializers.BaseSerializer):

    def to_representation(self, instance):
        timestamp_ms = time.mktime(instance.date.timetuple()) * 1000
        return {
            "id": instance.pk,
            "url": self._context['request'].build_absolute_uri(
                reverse('banktransactions:banktransaction-detail', kwargs={
                    'pk': instance.pk,
                }),
            ),
            "title": "{label}, {amount}".format(
                label=instance.label,
                amount=localize_signed_amount_currency(
                    instance.amount,
                    instance.currency,
                ),
            ),
            "class": "event-important" if instance.amount < 0 else "event-success",
            "start": timestamp_ms,
            "end": timestamp_ms,
            "extra_data": {
                "label": instance.label,
                "balance_total": instance.balance_total,
                "balance_total_view": localize_signed_amount(
                    instance.balance_total,
                ) if instance.balance_total is not None else None,
                "balance_reconciled": instance.balance_reconciled,
                "balance_reconciled_view": localize_signed_amount(
                    instance.balance_reconciled,
                ) if instance.balance_reconciled is not None else None,
            },
        }
