import datetime
from decimal import Decimal
from unittest import mock

from django.test import TestCase

from mymoney.api.bankaccounts.factories import BankAccountFactory
from mymoney.api.bankaccounts.models import BankAccount
from mymoney.banktransactiontags import BankTransactionTagFactory

from ..factories import BankTransactionFactory
from ..models import BankTransaction


class BankTransactionModelTestCase(TestCase):

    def test_status_inactive_create(self):
        bankaccount = BankAccountFactory(balance=100)

        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=Decimal('150'),
            status=BankTransaction.STATUS_INACTIVE
        )
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal(100))

    def test_status_inactive_update(self):
        bankaccount = BankAccountFactory(balance=100)

        banktransaction = BankTransactionFactory(
            bankaccount=bankaccount,
            amount=Decimal('150'),
        )
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal('250'))

        banktransaction.status = BankTransaction.STATUS_INACTIVE
        banktransaction.amount = Decimal('180')
        banktransaction.save()
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal('250'))

    def test_force_currency(self):
        bankaccount = BankAccountFactory(currency='EUR')
        banktransaction = BankTransactionFactory(
            bankaccount=bankaccount,
            currency='USD',
        )
        self.assertEqual(banktransaction.currency, 'EUR')

    def test_insert(self):
        bankaccount = BankAccountFactory(balance=-10)

        BankTransactionFactory(
            bankaccount=bankaccount,
            amount='15.59',
        )
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal('5.59'))

    def test_insert_fail(self):
        bankaccount = BankAccountFactory(balance=0)

        with mock.patch.object(BankTransaction, 'save', side_effect=Exception('Bang')):
            with self.assertRaises(Exception):
                BankTransactionFactory(
                    bankaccount=bankaccount,
                    amount='15.59',
                )

        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, 0)

    def test_save_bankaccount_update_fail(self):
        bankaccount = BankAccountFactory(balance=0)

        with mock.patch.object(BankAccount, 'save', side_effect=Exception('Boom')):
            with self.assertRaises(Exception):
                BankTransactionFactory(
                    bankaccount=bankaccount,
                    amount='15.59',
                )

        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, 0)

    def test_update(self):
        bankaccount = BankAccountFactory(balance=-10)
        banktransaction = BankTransactionFactory(
            bankaccount=bankaccount,
            amount='15.59',
        )

        banktransaction.refresh_from_db()
        banktransaction.amount += Decimal('14.41')
        banktransaction.save()
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal('20'))

    def test_update_fail(self):
        bankaccount = BankAccountFactory(balance=0)
        banktransaction = BankTransactionFactory(
            bankaccount=bankaccount,
            amount='-10',
        )
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal(-10))

        with mock.patch.object(BankTransaction, 'save', side_effect=Exception('Bang')):
            with self.assertRaises(Exception):
                banktransaction.amount = -50
                banktransaction.save()

        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal(-10))

    def test_status_inactive_delete(self):
        bankaccount = BankAccountFactory(balance=100)

        banktransaction = BankTransactionFactory(
            bankaccount=bankaccount,
            amount=Decimal('150'),
            status=BankTransaction.STATUS_INACTIVE,
        )
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal('100'))

        BankTransactionFactory(bankaccount=bankaccount, amount=Decimal('50'))
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal('150'))

        banktransaction.delete()
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal('150'))

    def test_delete(self):
        bankaccount = BankAccountFactory(balance=50)

        banktransaction = BankTransactionFactory(
            bankaccount=bankaccount,
            amount='-25',
        )
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal(25))

        banktransaction.delete()
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal(50))

    def test_delete_fail(self):
        bankaccount = BankAccountFactory(balance=50)
        banktransaction = BankTransactionFactory(
            bankaccount=bankaccount,
            amount='-25',
        )

        with mock.patch.object(BankTransaction, 'delete', side_effect=Exception('Bang')):
            with self.assertRaises(Exception):
                banktransaction.delete()

        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal(25))

    def test_delete_bankaccount_update_fail(self):
        bankaccount = BankAccountFactory(balance=50)
        banktransaction = BankTransactionFactory(
            bankaccount=bankaccount,
            amount='-25',
        )
        banktransaction_pk = banktransaction.pk

        with mock.patch.object(BankAccount, 'save', side_effect=Exception('Boom')):
            with self.assertRaises(Exception):
                banktransaction.delete()

        self.assertTrue(BankTransaction.objects.get(pk=banktransaction_pk))
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal(25))


class BankTransactionManagerTestCase(TestCase):

    def test_current_balance_none(self):
        bankaccount = BankAccountFactory(balance=0)
        self.assertEqual(
            BankTransaction.objects.get_current_balance(bankaccount),
            0,
        )

    def test_current_balance_other_bankaccounts(self):
        bankaccount = BankAccountFactory(balance=0)
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=-15,
            date=datetime.date.today() - datetime.timedelta(5),
        )
        BankTransactionFactory(
            amount=-15,
            date=datetime.date.today() - datetime.timedelta(5),
        )
        self.assertEqual(
            BankTransaction.objects.get_current_balance(bankaccount),
            Decimal('-15'),
        )

    def test_current_balance_inactive(self):
        bankaccount = BankAccountFactory(balance=0)
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=-15,
            date=datetime.date.today() - datetime.timedelta(5),
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=-15,
            date=datetime.date.today() - datetime.timedelta(5),
            status=BankTransaction.STATUS_INACTIVE,
        )
        self.assertEqual(
            BankTransaction.objects.get_current_balance(bankaccount),
            Decimal('-15'),
        )

    def test_current_balance_future(self):
        bankaccount = BankAccountFactory(balance=0)
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=-15,
            date=datetime.date.today() - datetime.timedelta(5),
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=-15,
            date=datetime.date.today() + datetime.timedelta(5),
        )
        self.assertEqual(
            BankTransaction.objects.get_current_balance(bankaccount),
            Decimal('-15'),
        )

    def test_current_balance(self):
        bankaccount = BankAccountFactory(balance=0)
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=-15,
            date=datetime.date.today() - datetime.timedelta(5),
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=-15,
            date=datetime.date.today() - datetime.timedelta(5),
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=40,
            date=datetime.date.today() - datetime.timedelta(5),
        )
        self.assertEqual(
            BankTransaction.objects.get_current_balance(bankaccount),
            Decimal('10'),
        )

    def test_reconciled_balance_none(self):
        bankaccount = BankAccountFactory(balance=0)
        self.assertEqual(
            BankTransaction.objects.get_reconciled_balance(bankaccount),
            0,
        )

    def test_reconciled_balance_other_bankaccount(self):
        bankaccount = BankAccountFactory(balance=0)
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=-15,
            reconciled=True,
        )
        BankTransactionFactory(
            amount=-15,
            reconciled=True,
        )
        self.assertEqual(
            BankTransaction.objects.get_reconciled_balance(bankaccount),
            Decimal('-15'),
        )

    def test_reconciled_balance_unreconciled(self):
        bankaccount = BankAccountFactory(balance=0)
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=-15,
            reconciled=True,
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=-15,
            reconciled=False,
        )
        self.assertEqual(
            BankTransaction.objects.get_reconciled_balance(bankaccount),
            Decimal('-15'),
        )

    def test_reconciled_balance_inactive(self):
        bankaccount = BankAccountFactory(balance=0)
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=-15,
            reconciled=True,
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=-15,
            reconciled=True,
            status=BankTransaction.STATUS_INACTIVE,
        )
        self.assertEqual(
            BankTransaction.objects.get_reconciled_balance(bankaccount),
            Decimal('-15'),
        )

    def test_reconciled_balance(self):
        bankaccount = BankAccountFactory(balance=0)
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=-15,
            reconciled=True,
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=-15,
            reconciled=True,
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=40,
            reconciled=True,
        )
        self.assertEqual(
            BankTransaction.objects.get_reconciled_balance(bankaccount),
            Decimal('10'),
        )

    def test_total_unscheduled_period_none(self):
        bankaccount = BankAccountFactory(balance=0)
        self.assertEqual(
            BankTransaction.objects.get_total_unscheduled_period(bankaccount),
            0,
        )

    @mock.patch(
        'mymoney.api.banktransactions.models.timezone.now',
        return_value=datetime.date(2015, 10, 26))
    def test_total_unscheduled_period_other_bankaccount(self, mock_tz):
        bankaccount = BankAccountFactory(balance=0)
        BankTransactionFactory(
            bankaccount=bankaccount,
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=False,
        )
        BankTransactionFactory(
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=False,
        )
        self.assertEqual(
            BankTransaction.objects.get_total_unscheduled_period(bankaccount),
            Decimal('-15'),
        )

    @mock.patch(
        'mymoney.api.banktransactions.models.timezone.now',
        return_value=datetime.date(2015, 10, 26))
    def test_total_unscheduled_period_out_of_ranges(self, mock_tz):
        bankaccount = BankAccountFactory(balance=0)
        BankTransactionFactory(
            bankaccount=bankaccount,
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=False,
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            date=datetime.date(2015, 11, 26),
            amount=-15,
            scheduled=False,
        )
        self.assertEqual(
            BankTransaction.objects.get_total_unscheduled_period(bankaccount),
            Decimal('-15'),
        )

    @mock.patch(
        'mymoney.api.banktransactions.models.timezone.now',
        return_value=datetime.date(2015, 10, 26))
    def test_total_unscheduled_period_scheduled(self, mock_tz):
        bankaccount = BankAccountFactory(balance=0)
        BankTransactionFactory(
            bankaccount=bankaccount,
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=False,
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=True,
        )
        self.assertEqual(
            BankTransaction.objects.get_total_unscheduled_period(bankaccount),
            Decimal('-15'),
        )

    @mock.patch(
        'mymoney.api.banktransactions.models.timezone.now',
        return_value=datetime.date(2015, 10, 26))
    def test_total_unscheduled_period_inactive(self, mock_tz):
        bankaccount = BankAccountFactory(balance=0)
        BankTransactionFactory(
            bankaccount=bankaccount,
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=False,
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=False,
            status=BankTransaction.STATUS_INACTIVE,
        )
        self.assertEqual(
            BankTransaction.objects.get_total_unscheduled_period(bankaccount),
            Decimal('-15'),
        )

    @mock.patch(
        'mymoney.api.banktransactions.models.timezone.now',
        return_value=datetime.date(2015, 10, 26))
    def test_total_unscheduled_period(self, mock_tz):
        bankaccount = BankAccountFactory(balance=0)
        BankTransactionFactory(
            bankaccount=bankaccount,
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=False,
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            date=datetime.date(2015, 10, 26),
            amount=-15,
            scheduled=False,
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            date=datetime.date(2015, 10, 26),
            amount=40,
            scheduled=False,
        )
        self.assertEqual(
            BankTransaction.objects.get_total_unscheduled_period(bankaccount),
            Decimal('10'),
        )


class RelationshipTestCase(TestCase):

    def test_delete_bankaccount(self):

        bankaccount = BankAccountFactory()
        tag = BankTransactionTagFactory()
        banktransaction = BankTransactionFactory(bankaccount=bankaccount, tag=tag)

        bankaccount.delete()

        with self.assertRaises(BankTransaction.DoesNotExist):
            banktransaction.refresh_from_db()

        # Should not be deleted.
        tag.refresh_from_db()
        self.assertTrue(tag)
