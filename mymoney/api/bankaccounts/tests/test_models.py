from decimal import Decimal

from django.test import TestCase

from mymoney.api.users.factories import UserFactory

from ..factories import BankAccountFactory
from ..models import BankAccount


class BankAccountModelTestCase(TestCase):

    def test_insert_balances_equals(self):
        bankaccount = BankAccountFactory(
            balance=Decimal('0'),
            balance_initial=Decimal('0'),
        )
        self.assertEqual(bankaccount.balance, Decimal('0'))
        self.assertEqual(bankaccount.balance_initial, Decimal('0'))

        bankaccount = BankAccountFactory(
            balance=Decimal('10'),
            balance_initial=Decimal('10'),
        )
        self.assertEqual(bankaccount.balance, Decimal('10'))
        self.assertEqual(bankaccount.balance_initial, Decimal('10'))

    def test_insert_balance_initial_prior(self):

        bankaccount = BankAccountFactory(
            balance=Decimal('10'),
            balance_initial=Decimal('-10'),
        )
        self.assertEqual(bankaccount.balance, Decimal('-10'))
        self.assertEqual(bankaccount.balance_initial, Decimal('-10'))

        bankaccount = BankAccountFactory(
            balance=Decimal('10'),
            balance_initial=Decimal('20'),
        )
        self.assertEqual(bankaccount.balance, Decimal('20'))
        self.assertEqual(bankaccount.balance_initial, Decimal('20'))

        bankaccount = BankAccountFactory(
            balance=Decimal('0'),
            balance_initial=Decimal('-5'),
        )
        self.assertEqual(bankaccount.balance, Decimal('-5'))
        self.assertEqual(bankaccount.balance_initial, Decimal('-5'))

    def test_insert_balance_default(self):

        bankaccount = BankAccountFactory(
            balance=Decimal('10'),
            balance_initial=Decimal('0'),
        )
        self.assertEqual(bankaccount.balance, Decimal('10'))
        self.assertEqual(bankaccount.balance_initial, Decimal('0'))

        bankaccount = BankAccountFactory(
            balance=Decimal('10'),
            balance_initial=Decimal('0'),
        )
        self.assertEqual(bankaccount.balance, Decimal('10'))
        self.assertEqual(bankaccount.balance_initial, Decimal('0'))

        bankaccount = BankAccountFactory(
            balance=Decimal('-10'),
            balance_initial=Decimal('0'),
        )
        self.assertEqual(bankaccount.balance, Decimal('-10'))
        self.assertEqual(bankaccount.balance_initial, Decimal('0'))

    def test_balance_update(self):
        bankaccount = BankAccountFactory(
            balance=Decimal('0'),
            balance_initial=Decimal('0'),
        )

        bankaccount.balance = Decimal('10')
        bankaccount.save()
        self.assertEqual(bankaccount.balance, Decimal('10'))

        bankaccount.balance = Decimal('-20')
        bankaccount.save()
        self.assertEqual(bankaccount.balance, Decimal('-20'))

    def test_balance_update_float(self):
        """
        Using float is not supported. Use Decimal instead.
        """
        bankaccount = BankAccountFactory(
            balance=Decimal('0'),
            balance_initial=Decimal('0'),
        )

        bankaccount.balance = 10.10
        with self.assertRaises(TypeError):
            bankaccount.save()

    def test_balance_initial_update(self):
        bankaccount = BankAccountFactory(
            balance=Decimal('0'),
            balance_initial=Decimal('0'),
        )
        bankaccount.balance_initial = Decimal('10')
        bankaccount.save()
        self.assertEqual(bankaccount.balance, Decimal('10'))
        self.assertEqual(bankaccount.balance_initial, Decimal('10'))

        bankaccount.balance_initial = Decimal('-20')
        bankaccount.save()
        self.assertEqual(bankaccount.balance, Decimal('-20'))
        self.assertEqual(bankaccount.balance_initial, Decimal('-20'))

    def test_balance_initial_update_float(self):
        """
        Test unsupported operand type between float and decimal.
        """
        bankaccount = BankAccountFactory(
            balance=Decimal('0'),
            balance_initial=Decimal('0'),
        )
        bankaccount.balance_initial = -10.0
        bankaccount.save()
        self.assertEqual(bankaccount.balance, Decimal('-10'))
        self.assertEqual(bankaccount.balance_initial, Decimal('-10'))

    def test_balance_and_balance_initial_update(self):
        bankaccount = BankAccountFactory(
            balance=Decimal('0'),
            balance_initial=Decimal('0'),
        )

        bankaccount.balance = Decimal('10')
        bankaccount.balance_initial = Decimal('10')
        bankaccount.save()
        self.assertEqual(bankaccount.balance, Decimal('20'))
        self.assertEqual(bankaccount.balance_initial, Decimal('10'))

        bankaccount.balance = Decimal('0')
        bankaccount.balance_initial = Decimal('-20')
        bankaccount.save()
        self.assertEqual(bankaccount.balance, Decimal('-30'))
        self.assertEqual(bankaccount.balance_initial, Decimal('-20'))


class BankAccountManagerTestCase(TestCase):

    def tearDown(self):
        BankAccount.objects.all().delete()

    def test_delete_no_orphan(self):
        BankAccountFactory(owners=[UserFactory()])
        self.assertEqual(BankAccount.objects.all().count(), 1)
        BankAccount.objects.delete_orphans()
        self.assertEqual(BankAccount.objects.all().count(), 1)

    def test_delete_orphans(self):
        BankAccountFactory()
        self.assertEqual(BankAccount.objects.all().count(), 1)
        BankAccount.objects.delete_orphans()
        self.assertEqual(BankAccount.objects.all().count(), 0)
