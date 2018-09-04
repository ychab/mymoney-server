import datetime
import time
from decimal import Decimal

from django.test import TestCase, override_settings

from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory

from mymoney.api.bankaccounts.factories import BankAccountFactory

from ..factories import BankTransactionFactory
from ..models import BankTransaction
from ..serializers import (
    BankTransactionDetailExtraSerializer, BankTransactionDetailSerializer,
    BankTransactionEventInputSerializer, BankTransactionEventOutputSerializer,
)


class BankTransactionDetailSerializerTestCase(TestCase):

    @override_settings(LANGUAGE_CODE='en-us')
    def test_date_format_localize_en_us(self):
        banktransaction = BankTransactionFactory(date=datetime.date(2015, 11, 30))
        serializer = BankTransactionDetailSerializer(banktransaction)
        self.assertEqual(
            serializer.data['date_view'],
            '11/30/2015',
        )

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_date_format_localize_fr_fr(self):
        banktransaction = BankTransactionFactory(date=datetime.date(2015, 11, 30))
        serializer = BankTransactionDetailSerializer(banktransaction)
        self.assertEqual(
            serializer.data['date_view'],
            '30/11/2015',
        )

    @override_settings(LANGUAGE_CODE='en-us')
    def test_localize_amount_en_us(self):
        banktransaction = BankTransactionFactory(amount=15.23)
        serializer = BankTransactionDetailSerializer(banktransaction)
        self.assertEqual(
            serializer.data['amount_localized'],
            '+15.23',
        )

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_localize_amount_fr_fr(self):
        banktransaction = BankTransactionFactory(amount=15.23)
        serializer = BankTransactionDetailSerializer(banktransaction)
        self.assertEqual(
            serializer.data['amount_localized'],
            '+15,23',
        )

    @override_settings(LANGUAGE_CODE='en-us')
    def test_localize_currency_en_us(self):
        bankaccount = BankAccountFactory(currency='USD')
        banktransaction = BankTransactionFactory(
            bankaccount=bankaccount, amount=1547.23)

        serializer = BankTransactionDetailSerializer(banktransaction)
        self.assertEqual(
            serializer.data['amount_currency'],
            "+$1,547.23",
        )

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_localize_currency_fr_fr(self):
        bankaccount = BankAccountFactory(currency='EUR')
        banktransaction = BankTransactionFactory(
            bankaccount=bankaccount, amount=1547.23)

        serializer = BankTransactionDetailSerializer(banktransaction)
        self.assertEqual(
            serializer.data['amount_currency'],
            '+1\xa0547,23\xa0€',
        )

    @override_settings(LANGUAGE_CODE='en-us')
    def test_payment_method_label_localize_en_us(self):
        banktransaction = BankTransactionFactory(
            payment_method=BankTransaction.PAYMENT_METHOD_CASH)
        serializer = BankTransactionDetailSerializer(banktransaction)
        self.assertEqual(
            serializer.data['payment_method_display'],
            'Cash',
        )

    @override_settings(LANGUAGE_CODE='en-us')
    def test_status_label_localize_en_us(self):
        banktransaction = BankTransactionFactory(
            status=BankTransaction.STATUS_IGNORED)
        serializer = BankTransactionDetailSerializer(banktransaction)
        self.assertEqual(
            serializer.data['status_display'],
            'Ignored',
        )


class BankTransactionDetailExtraSerializerTestCase(TestCase):

    @override_settings(LANGUAGE_CODE='en-us')
    def test_balance_total_localize_en_us(self):
        banktransaction = BankTransactionFactory()
        banktransaction.balance_total = Decimal('20.15')
        banktransaction.balance_reconciled = Decimal('20.15')

        serializer = BankTransactionDetailExtraSerializer(banktransaction)
        self.assertEqual(
            serializer.data['balance_total_view'],
            '+20.15',
        )

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_balance_total_localize_fr_fr(self):
        banktransaction = BankTransactionFactory()
        banktransaction.balance_total = Decimal('20.15')
        banktransaction.balance_reconciled = Decimal('20.15')

        serializer = BankTransactionDetailExtraSerializer(banktransaction)
        self.assertEqual(
            serializer.data['balance_total_view'],
            '+20,15',
        )

    @override_settings(LANGUAGE_CODE='en-us')
    def test_balance_reconciled_localize_en_us(self):
        banktransaction = BankTransactionFactory()
        banktransaction.balance_total = Decimal('20.15')
        banktransaction.balance_reconciled = Decimal('20.15')

        serializer = BankTransactionDetailExtraSerializer(banktransaction)
        self.assertEqual(
            serializer.data['balance_reconciled_view'],
            '+20.15',
        )

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_balance_reconciled_localize_fr_fr(self):
        banktransaction = BankTransactionFactory()
        banktransaction.balance_reconciled = Decimal('20.15')
        banktransaction.balance_total = Decimal('20.15')

        serializer = BankTransactionDetailExtraSerializer(banktransaction)
        self.assertEqual(
            serializer.data['balance_reconciled_view'],
            '+20,15',
        )


class BankTransactionEventInputSerializerTestCase(TestCase):

    def test_date_ranges_validator(self):
        datetime_from = datetime.datetime(2015, 10, 29, 0, 0, 0, 0)
        datetime_to = datetime.datetime(2015, 10, 28, 0, 0, 0, 0)

        serializer = BankTransactionEventInputSerializer(data={
            'date_from': time.mktime(datetime_from.timetuple()) * 1000,
            'date_to': time.mktime(datetime_to.timetuple()) * 1000,
        })
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)


class BankTransactionEventOutputSerializerTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.context = {'request': APIRequestFactory().request()}

    def test_representation_uri(self):
        banktransaction = BankTransactionFactory()
        banktransaction.balance_total = 0
        banktransaction.balance_reconciled = 0

        serializer = BankTransactionEventOutputSerializer(
            banktransaction, context=self.context)

        self.assertEqual(
            serializer.data['url'],
            'http://testserver{path}'.format(
                path=reverse('banktransactions:banktransaction-detail', kwargs={
                    'pk': banktransaction.pk,
                })
            )
        )

    def test_representation_extra_balance_none(self):
        banktransaction = BankTransactionFactory()
        banktransaction.balance_total = None
        banktransaction.balance_reconciled = None

        serializer = BankTransactionEventOutputSerializer(
            banktransaction, context=self.context)

        self.assertIsNone(serializer.data['extra_data']['balance_total'])
        self.assertIsNone(serializer.data['extra_data']['balance_reconciled'])

    def test_representation_timestamp_millisecond(self):
        banktransaction = BankTransactionFactory(date=datetime.date(2015, 10, 29))
        banktransaction.balance_total = 0
        banktransaction.balance_reconciled = 0

        serializer = BankTransactionEventOutputSerializer(
            banktransaction, context=self.context)

        self.assertEqual(serializer.data['start'], 1446076800000.0)
        self.assertEqual(serializer.data['end'], 1446076800000.0)
