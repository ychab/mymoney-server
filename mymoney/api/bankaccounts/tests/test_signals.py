from django.test import TestCase

from mymoney.api.users.factories import UserFactory

from ..factories import BankAccountFactory
from ..models import BankAccount


class SignalsTestCase(TestCase):

    def test_signal_delete_orphan(self):

        owner = UserFactory()
        bankaccount = BankAccountFactory(owners=[owner])
        owner.delete()

        with self.assertRaises(BankAccount.DoesNotExist):
            bankaccount.refresh_from_db()

    def test_signal_delete_not_orphan(self):

        owner = UserFactory()
        bankaccount = BankAccountFactory(owners=[owner, UserFactory()])
        owner.delete()

        bankaccount.refresh_from_db()
        self.assertTrue(bankaccount)
