from unittest import mock

from django.test import TestCase

from rest_framework import exceptions

from mymoney.bankaccounts import BankAccountFactory
from mymoney.api.users.factories import UserFactory

from ..factories import BankTransactionFactory
from ..validators import BankTransactionOwnerValidator


class BankTransactionOwnerValidatorTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.bankaccount = BankAccountFactory(owners=[cls.user])

    def test_no_value(self):
        validator = BankTransactionOwnerValidator('ids')
        validator({})

    @mock.patch(
        'mymoney.api.banktransactions.validators.BankTransactionOwnerValidator.MAX', 2)
    def test_max_exceed(self):
        validator = BankTransactionOwnerValidator('ids')
        with self.assertRaises(exceptions.ValidationError):
            validator({'ids': (1, 2, 3)})

    def test_not_owner_all_banktransactions(self):
        banktransaction = BankTransactionFactory()
        validator = BankTransactionOwnerValidator('ids')
        validator.set_context(mock.Mock(context={'request': mock.Mock(user=self.user)}))
        with self.assertRaises(exceptions.ValidationError):
            validator({'ids': (banktransaction,)})

    def test_not_owner_some_banktransactions(self):
        bt1 = BankTransactionFactory()
        bt2 = BankTransactionFactory(bankaccount=self.bankaccount)
        validator = BankTransactionOwnerValidator('ids')
        validator.set_context(mock.Mock(context={'request': mock.Mock(user=self.user)}))
        with self.assertRaises(exceptions.ValidationError):
            validator({'ids': (bt1, bt2)})

    def test_valid(self):
        bt1 = BankTransactionFactory(bankaccount=self.bankaccount)
        bt2 = BankTransactionFactory(bankaccount=self.bankaccount)
        validator = BankTransactionOwnerValidator('ids')
        validator.set_context(mock.Mock(context={'request': mock.Mock(user=self.user)}))
        validator({'ids': (bt1, bt2)})
