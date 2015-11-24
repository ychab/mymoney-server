import datetime
from decimal import Decimal

from django.test import TestCase, override_settings

from dateutil.relativedelta import relativedelta

from mymoney.api.banktransactions.factories import BankTransactionFactory

from ..factories import BankAccountFactory
from ..serializers import BankAccountDetailSerializer, BankAccountSerializer


class BankAccountSerializerTestCase(TestCase):

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_balance_view_french(self):
        bankaccount = BankAccountFactory(currency='EUR', balance=Decimal('-15.23'))
        serializer = BankAccountSerializer(bankaccount)
        self.assertEqual(serializer.data['balance_view'], '-15,23\xa0€')

    @override_settings(LANGUAGE_CODE='en-us')
    def test_balance_view_usa(self):
        bankaccount = BankAccountFactory(currency='USD', balance=Decimal('-15.23'))
        serializer = BankAccountSerializer(bankaccount)
        self.assertEqual(serializer.data['balance_view'], '-$15.23')


class BankAccountDetailSerializerTestCase(TestCase):

    @override_settings(LANGUAGE_CODE='en-us')
    def test_balance_current(self):
        bankaccount = BankAccountFactory(balance=0)
        BankTransactionFactory(
            bankaccount=bankaccount,
            date=datetime.date.today(),
            amount=10,
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            date=datetime.date.today(),
            amount=10,
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            date=datetime.date.today() + relativedelta(days=5),
            amount=10,
        )
        serializer = BankAccountDetailSerializer(bankaccount)
        self.assertEqual(serializer.data['balance_current'], '20.00')

    @override_settings(LANGUAGE_CODE='en-us')
    def test_balance_reconciled(self):
        bankaccount = BankAccountFactory(balance=0)
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
            reconciled=True,
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
            reconciled=True,
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
            reconciled=False,
        )
        serializer = BankAccountDetailSerializer(bankaccount)
        self.assertEqual(serializer.data['balance_reconciled'], '20.00')
