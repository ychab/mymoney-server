import datetime
from decimal import Decimal
from unittest import mock

from django.test import TestCase

from mymoney.accounts.factories import AccountFactory
from mymoney.accounts.models import Account
from mymoney.tags.factories import TagFactory

from ..factories import TransactionFactory
from ..models import Transaction


class TransactionModelTestCase(TestCase):

    def test_status_inactive_create(self):
        account = AccountFactory(balance=100)

        TransactionFactory(
            account=account,
            amount=Decimal('150'),
            status=Transaction.STATUS_INACTIVE
        )
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal(100))

    def test_status_inactive_update(self):
        account = AccountFactory(balance=100)

        transaction = TransactionFactory(
            account=account,
            amount=Decimal('150'),
        )
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('250'))

        transaction.status = Transaction.STATUS_INACTIVE
        transaction.amount = Decimal('180')
        transaction.save()
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('250'))

    def test_force_currency(self):
        account = AccountFactory(currency='EUR')
        transaction = TransactionFactory(
            account=account,
            currency='USD',
        )
        self.assertEqual(transaction.currency, 'EUR')

    def test_insert(self):
        account = AccountFactory(balance=-10)

        TransactionFactory(
            account=account,
            amount='15.59',
        )
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('5.59'))

    def test_insert_fail(self):
        account = AccountFactory(balance=0)

        with mock.patch.object(Transaction, 'save', side_effect=Exception('Bang')):
            with self.assertRaises(Exception):
                TransactionFactory(
                    account=account,
                    amount='15.59',
                )

        account.refresh_from_db()
        self.assertEqual(account.balance, 0)

    def test_save_account_update_fail(self):
        account = AccountFactory(balance=0)

        with mock.patch.object(Account, 'save', side_effect=Exception('Boom')):
            with self.assertRaises(Exception):
                TransactionFactory(
                    account=account,
                    amount='15.59',
                )

        account.refresh_from_db()
        self.assertEqual(account.balance, 0)

    def test_update(self):
        account = AccountFactory(balance=-10)
        transaction = TransactionFactory(
            account=account,
            amount='15.59',
        )

        transaction.refresh_from_db()
        transaction.amount += Decimal('14.41')
        transaction.save()
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('20'))

    def test_update_fail(self):
        account = AccountFactory(balance=0)
        transaction = TransactionFactory(
            account=account,
            amount='-10',
        )
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal(-10))

        with mock.patch.object(Transaction, 'save', side_effect=Exception('Bang')):
            with self.assertRaises(Exception):
                transaction.amount = -50
                transaction.save()

        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal(-10))

    def test_status_inactive_delete(self):
        account = AccountFactory(balance=100)

        transaction = TransactionFactory(
            account=account,
            amount=Decimal('150'),
            status=Transaction.STATUS_INACTIVE,
        )
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('100'))

        TransactionFactory(account=account, amount=Decimal('50'))
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('150'))

        transaction.delete()
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('150'))

    def test_delete(self):
        account = AccountFactory(balance=50)

        transaction = TransactionFactory(
            account=account,
            amount='-25',
        )
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal(25))

        transaction.delete()
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal(50))

    def test_delete_fail(self):
        account = AccountFactory(balance=50)
        transaction = TransactionFactory(
            account=account,
            amount='-25',
        )

        with mock.patch.object(Transaction, 'delete', side_effect=Exception('Bang')):
            with self.assertRaises(Exception):
                transaction.delete()

        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal(25))

    def test_delete_account_update_fail(self):
        account = AccountFactory(balance=50)
        transaction = TransactionFactory(
            account=account,
            amount='-25',
        )
        transaction_pk = transaction.pk

        with mock.patch.object(Account, 'save', side_effect=Exception('Boom')):
            with self.assertRaises(Exception):
                transaction.delete()

        self.assertTrue(Transaction.objects.get(pk=transaction_pk))
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal(25))


class TransactionManagerTestCase(TestCase):

    def test_current_balance_none(self):
        account = AccountFactory(balance=0)
        self.assertEqual(
            Transaction.objects.get_current_balance(account),
            0,
        )

    def test_current_balance_other_accounts(self):
        account = AccountFactory(balance=0)
        TransactionFactory(
            account=account,
            amount=-15,
            date=datetime.date.today() - datetime.timedelta(5),
        )
        TransactionFactory(
            amount=-15,
            date=datetime.date.today() - datetime.timedelta(5),
        )
        self.assertEqual(
            Transaction.objects.get_current_balance(account),
            Decimal('-15'),
        )

    def test_current_balance_inactive(self):
        account = AccountFactory(balance=0)
        TransactionFactory(
            account=account,
            amount=-15,
            date=datetime.date.today() - datetime.timedelta(5),
        )
        TransactionFactory(
            account=account,
            amount=-15,
            date=datetime.date.today() - datetime.timedelta(5),
            status=Transaction.STATUS_INACTIVE,
        )
        self.assertEqual(
            Transaction.objects.get_current_balance(account),
            Decimal('-15'),
        )

    def test_current_balance_future(self):
        account = AccountFactory(balance=0)
        TransactionFactory(
            account=account,
            amount=-15,
            date=datetime.date.today() - datetime.timedelta(5),
        )
        TransactionFactory(
            account=account,
            amount=-15,
            date=datetime.date.today() + datetime.timedelta(5),
        )
        self.assertEqual(
            Transaction.objects.get_current_balance(account),
            Decimal('-15'),
        )

    def test_current_balance(self):
        account = AccountFactory(balance=0)
        TransactionFactory(
            account=account,
            amount=-15,
            date=datetime.date.today() - datetime.timedelta(5),
        )
        TransactionFactory(
            account=account,
            amount=-15,
            date=datetime.date.today() - datetime.timedelta(5),
        )
        TransactionFactory(
            account=account,
            amount=40,
            date=datetime.date.today() - datetime.timedelta(5),
        )
        self.assertEqual(
            Transaction.objects.get_current_balance(account),
            Decimal('10'),
        )

    def test_reconciled_balance_none(self):
        account = AccountFactory(balance=0)
        self.assertEqual(
            Transaction.objects.get_reconciled_balance(account),
            0,
        )

    def test_reconciled_balance_other_account(self):
        account = AccountFactory(balance=0)
        TransactionFactory(
            account=account,
            amount=-15,
            reconciled=True,
        )
        TransactionFactory(
            amount=-15,
            reconciled=True,
        )
        self.assertEqual(
            Transaction.objects.get_reconciled_balance(account),
            Decimal('-15'),
        )

    def test_reconciled_balance_unreconciled(self):
        account = AccountFactory(balance=0)
        TransactionFactory(
            account=account,
            amount=-15,
            reconciled=True,
        )
        TransactionFactory(
            account=account,
            amount=-15,
            reconciled=False,
        )
        self.assertEqual(
            Transaction.objects.get_reconciled_balance(account),
            Decimal('-15'),
        )

    def test_reconciled_balance_inactive(self):
        account = AccountFactory(balance=0)
        TransactionFactory(
            account=account,
            amount=-15,
            reconciled=True,
        )
        TransactionFactory(
            account=account,
            amount=-15,
            reconciled=True,
            status=Transaction.STATUS_INACTIVE,
        )
        self.assertEqual(
            Transaction.objects.get_reconciled_balance(account),
            Decimal('-15'),
        )

    def test_reconciled_balance(self):
        account = AccountFactory(balance=0)
        TransactionFactory(
            account=account,
            amount=-15,
            reconciled=True,
        )
        TransactionFactory(
            account=account,
            amount=-15,
            reconciled=True,
        )
        TransactionFactory(
            account=account,
            amount=40,
            reconciled=True,
        )
        self.assertEqual(
            Transaction.objects.get_reconciled_balance(account),
            Decimal('10'),
        )

    def test_total_unscheduled_period_none(self):
        account = AccountFactory(balance=0)
        self.assertEqual(
            Transaction.objects.get_total_unscheduled_period(account),
            0,
        )

    @mock.patch(
        'mymoney.transactions.models.timezone.now',
        return_value=datetime.date(2015, 10, 26))
    def test_total_unscheduled_period_other_account(self, mock_tz):
        account = AccountFactory(balance=0)
        TransactionFactory(
            account=account,
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=False,
        )
        TransactionFactory(
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=False,
        )
        self.assertEqual(
            Transaction.objects.get_total_unscheduled_period(account),
            Decimal('-15'),
        )

    @mock.patch(
        'mymoney.transactions.models.timezone.now',
        return_value=datetime.date(2015, 10, 26))
    def test_total_unscheduled_period_out_of_ranges(self, mock_tz):
        account = AccountFactory(balance=0)
        TransactionFactory(
            account=account,
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=False,
        )
        TransactionFactory(
            account=account,
            date=datetime.date(2015, 11, 26),
            amount=-15,
            scheduled=False,
        )
        self.assertEqual(
            Transaction.objects.get_total_unscheduled_period(account),
            Decimal('-15'),
        )

    @mock.patch(
        'mymoney.transactions.models.timezone.now',
        return_value=datetime.date(2015, 10, 26))
    def test_total_unscheduled_period_scheduled(self, mock_tz):
        account = AccountFactory(balance=0)
        TransactionFactory(
            account=account,
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=False,
        )
        TransactionFactory(
            account=account,
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=True,
        )
        self.assertEqual(
            Transaction.objects.get_total_unscheduled_period(account),
            Decimal('-15'),
        )

    @mock.patch(
        'mymoney.transactions.models.timezone.now',
        return_value=datetime.date(2015, 10, 26))
    def test_total_unscheduled_period_inactive(self, mock_tz):
        account = AccountFactory(balance=0)
        TransactionFactory(
            account=account,
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=False,
        )
        TransactionFactory(
            account=account,
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=False,
            status=Transaction.STATUS_INACTIVE,
        )
        self.assertEqual(
            Transaction.objects.get_total_unscheduled_period(account),
            Decimal('-15'),
        )

    @mock.patch(
        'mymoney.transactions.models.timezone.now',
        return_value=datetime.date(2015, 10, 26))
    def test_total_unscheduled_period(self, mock_tz):
        account = AccountFactory(balance=0)
        TransactionFactory(
            account=account,
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=False,
        )
        TransactionFactory(
            account=account,
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=False,
        )
        TransactionFactory(
            account=account,
            date=datetime.date(2015, 10, 26),
            amount=40,
            scheduled=False,
        )
        self.assertEqual(
            Transaction.objects.get_total_unscheduled_period(account),
            Decimal('10'),
        )


class RelationshipTestCase(TestCase):

    def test_delete_account(self):

        account = AccountFactory()
        tag = TagFactory()
        transaction = TransactionFactory(account=account, tag=tag)

        account.delete()

        with self.assertRaises(Transaction.DoesNotExist):
            transaction.refresh_from_db()

        # Should not be deleted.
        tag.refresh_from_db()
        self.assertTrue(tag)
