import datetime
from decimal import Decimal

from django.test import TestCase, override_settings

from mymoney.accounts.factories import AccountFactory

from ..factories import TransactionFactory
from ..models import Transaction
from ..serializers import (
    TransactionDetailSerializer, TransactionListSerializer,
)


class TransactionDetailSerializerTestCase(TestCase):

    @override_settings(LANGUAGE_CODE='en-us')
    def test_date_format_localize_en_us(self):
        transaction = TransactionFactory(date=datetime.date(2015, 11, 30))
        serializer = TransactionDetailSerializer(transaction)
        self.assertEqual(
            serializer.data['date_view'],
            '11/30/2015',
        )

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_date_format_localize_fr_fr(self):
        transaction = TransactionFactory(date=datetime.date(2015, 11, 30))
        serializer = TransactionDetailSerializer(transaction)
        self.assertEqual(
            serializer.data['date_view'],
            '30/11/2015',
        )

    @override_settings(LANGUAGE_CODE='en-us')
    def test_localize_amount_en_us(self):
        transaction = TransactionFactory(amount=15.23)
        serializer = TransactionDetailSerializer(transaction)
        self.assertEqual(
            serializer.data['amount_localized'],
            '+15.23',
        )

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_localize_amount_fr_fr(self):
        transaction = TransactionFactory(amount=15.23)
        serializer = TransactionDetailSerializer(transaction)
        self.assertEqual(
            serializer.data['amount_localized'],
            '+15,23',
        )

    @override_settings(LANGUAGE_CODE='en-us')
    def test_localize_currency_en_us(self):
        account = AccountFactory(currency='USD')
        transaction = TransactionFactory(
            account=account, amount=1547.23)

        serializer = TransactionDetailSerializer(transaction)
        self.assertEqual(
            serializer.data['amount_currency'],
            "+$1,547.23",
        )

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_localize_currency_fr_fr(self):
        account = AccountFactory(currency='EUR')
        transaction = TransactionFactory(
            account=account, amount=1547.23)

        serializer = TransactionDetailSerializer(transaction)
        self.assertEqual(
            serializer.data['amount_currency'],
            '+1\xa0547,23\xa0€',
        )

    @override_settings(LANGUAGE_CODE='en-us')
    def test_payment_method_label_localize_en_us(self):
        transaction = TransactionFactory(
            payment_method=Transaction.PAYMENT_METHOD_CASH)
        serializer = TransactionDetailSerializer(transaction)
        self.assertEqual(
            serializer.data['payment_method_display'],
            'Cash',
        )

    @override_settings(LANGUAGE_CODE='en-us')
    def test_status_label_localize_en_us(self):
        transaction = TransactionFactory(
            status=Transaction.STATUS_IGNORED)
        serializer = TransactionDetailSerializer(transaction)
        self.assertEqual(
            serializer.data['status_display'],
            'Ignored',
        )


class TransactionListSerializerTestCase(TestCase):

    @override_settings(LANGUAGE_CODE='en-us')
    def test_balance_total_localize_en_us(self):
        transaction = TransactionFactory()
        transaction.balance_total = Decimal('20.15')
        transaction.balance_reconciled = Decimal('20.15')

        serializer = TransactionListSerializer(transaction)
        self.assertEqual(
            serializer.data['balance_total_view'],
            '+20.15',
        )

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_balance_total_localize_fr_fr(self):
        transaction = TransactionFactory()
        transaction.balance_total = Decimal('20.15')
        transaction.balance_reconciled = Decimal('20.15')

        serializer = TransactionListSerializer(transaction)
        self.assertEqual(
            serializer.data['balance_total_view'],
            '+20,15',
        )

    @override_settings(LANGUAGE_CODE='en-us')
    def test_balance_reconciled_localize_en_us(self):
        transaction = TransactionFactory()
        transaction.balance_total = Decimal('20.15')
        transaction.balance_reconciled = Decimal('20.15')

        serializer = TransactionListSerializer(transaction)
        self.assertEqual(
            serializer.data['balance_reconciled_view'],
            '+20.15',
        )

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_balance_reconciled_localize_fr_fr(self):
        transaction = TransactionFactory()
        transaction.balance_reconciled = Decimal('20.15')
        transaction.balance_total = Decimal('20.15')

        serializer = TransactionListSerializer(transaction)
        self.assertEqual(
            serializer.data['balance_reconciled_view'],
            '+20,15',
        )
