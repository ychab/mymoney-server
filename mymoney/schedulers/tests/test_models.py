import datetime
from decimal import Decimal
from unittest.mock import patch

from django.db.models import QuerySet
from django.test import TestCase, override_settings
from django.utils import timezone

from mymoney.bankaccounts import BankAccountFactory
from mymoney.banktransactions import BankTransaction
from mymoney.banktransactiontags import BankTransactionTagFactory

from ..factories import BankTransactionSchedulerFactory
from ..models import BankTransactionScheduler


class BankTransactionSchedulerModelTestCase(TestCase):

    def tearDown(self):
        BankTransaction.objects.all().delete()

    def test_clone_field_date_weekly(self):
        bts = BankTransactionSchedulerFactory(
            date=datetime.date(2015, 3, 26),
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        bts.clone()
        self.assertEqual(BankTransaction.objects.count(), 1)
        bt_clone = BankTransaction.objects.first()
        self.assertEqual(bt_clone.date, datetime.date(2015, 4, 2))

    def test_clone_field_date_monthly(self):
        bts = BankTransactionSchedulerFactory(
            date=datetime.date(2015, 1, 31),
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        bts.clone()
        self.assertEqual(BankTransaction.objects.count(), 1)
        bt_clone = BankTransaction.objects.first()
        self.assertEqual(bt_clone.date, datetime.date(2015, 2, 28))

    def test_clone_field_currency(self):
        bankaccount = BankAccountFactory(balance=0, currency='EUR')
        bts = BankTransactionSchedulerFactory(bankaccount=bankaccount)
        bts.clone()
        self.assertEqual(BankTransaction.objects.count(), 1)
        bt_clone = BankTransaction.objects.first()
        self.assertEqual(bt_clone.currency, bts.currency)
        self.assertEqual(bt_clone.currency, bankaccount.currency)

    def test_clone_field_reconciled(self):
        bts = BankTransactionSchedulerFactory(reconciled=True)
        bts.clone()
        self.assertEqual(BankTransaction.objects.count(), 1)
        bt_clone = BankTransaction.objects.first()
        self.assertFalse(bt_clone.reconciled)

    def test_clone_field_scheduled(self):
        bts = BankTransactionSchedulerFactory()
        bts.clone()
        self.assertEqual(BankTransaction.objects.count(), 1)
        bt_clone = BankTransaction.objects.first()
        self.assertTrue(bt_clone.scheduled)

    def test_clone_fields(self):
        bankaccount = BankAccountFactory()
        bts = BankTransactionSchedulerFactory(
            label="foo",
            bankaccount=bankaccount,
            amount=Decimal('10.23'),
            status=BankTransaction.STATUS_ACTIVE,
            reconciled=True,
            payment_method=BankTransaction.PAYMENT_METHOD_CASH,
            memo="Test",
            tag=BankTransactionTagFactory(),
        )
        bts.clone()
        self.assertEqual(BankTransaction.objects.count(), 1)
        bt_clone = BankTransaction.objects.first()
        self.assertEqual(bt_clone.label, bts.label)
        self.assertEqual(bt_clone.bankaccount, bts.bankaccount)
        self.assertEqual(bt_clone.amount, bts.amount)
        self.assertEqual(bt_clone.status, bts.status)
        self.assertEqual(bt_clone.payment_method, bts.payment_method)
        self.assertEqual(bt_clone.memo, bts.memo)
        self.assertEqual(bt_clone.tag.pk, bts.tag.pk)

    def test_bankaccount_balance(self):
        bankaccount = BankAccountFactory(balance=0)
        bts = BankTransactionSchedulerFactory(
            bankaccount=bankaccount,
            amount=10,
            status=BankTransactionScheduler.STATUS_ACTIVE,
        )
        bts.clone()
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal(10))

    def test_clone_recurrence_decrement(self):
        bts = BankTransactionSchedulerFactory(recurrence=2)
        bts.clone()
        bts.refresh_from_db()
        self.assertEqual(bts.recurrence, 1)

    def test_clone_recurrence_infinite(self):
        bts = BankTransactionSchedulerFactory(recurrence=None)
        bts.clone()
        bts.refresh_from_db()
        self.assertIsNone(bts.recurrence)

    def test_clone_scheduler_delete(self):
        bts = BankTransactionSchedulerFactory(recurrence=1)
        bts.clone()
        with self.assertRaises(BankTransactionScheduler.DoesNotExist):
            bts.refresh_from_db()

    def test_clone_scheduler_date_monthly(self):
        bts = BankTransactionSchedulerFactory(
            date=datetime.date(2015, 1, 31),
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        bts.clone()
        bts.refresh_from_db()
        self.assertEqual(bts.date, datetime.date(2015, 2, 28))

    def test_clone_scheduler_date_weekly(self):
        bts = BankTransactionSchedulerFactory(
            date=datetime.date(2015, 3, 26),
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        bts.clone()
        bts.refresh_from_db()
        self.assertEqual(bts.date, datetime.date(2015, 4, 2))

    @patch('mymoney.api.banktransactionschedulers.models.timezone.now')
    def test_clone_scheduler_last_action(self, mock_now):
        dtime = datetime.datetime(2015, 10, 31, 0, 0, 0, 0, tzinfo=timezone.utc)
        mock_now.return_value = dtime
        bts = BankTransactionSchedulerFactory(
            last_action=None,
        )
        bts.clone()
        bts.refresh_from_db()
        self.assertEqual(bts.last_action, dtime)

    def test_clone_scheduler_state(self):
        bts = BankTransactionSchedulerFactory(
            state=BankTransactionScheduler.STATE_WAITING,
        )
        bts.clone()
        bts.refresh_from_db()
        self.assertEqual(bts.state, BankTransactionScheduler.STATE_FINISHED)

    @patch(
        'mymoney.api.banktransactionschedulers.models.BankTransaction.objects.create',
        side_effect=Exception('Boom'),
    )
    def test_clone_banktransaction_create_fail(self, mock_method):
        bts = BankTransactionSchedulerFactory(
            state=BankTransactionScheduler.STATE_WAITING,
        )
        with self.assertLogs(logger='mymoney.errors', level='ERROR'):
            bts.clone()
        bts.refresh_from_db()
        self.assertEqual(bts.state, BankTransactionScheduler.STATE_FAILED)

    @patch.object(BankTransactionScheduler, 'delete', side_effect=Exception('Boom'))
    def test_clone_scheduler_delete_fail(self, mock_method):
        bts = BankTransactionSchedulerFactory(
            recurrence=1,
            state=BankTransactionScheduler.STATE_WAITING,
        )
        with self.assertLogs(logger='mymoney.errors', level='ERROR'):
            bts.clone()
        bts.refresh_from_db()
        self.assertEqual(bts.state, BankTransactionScheduler.STATE_FAILED)
        self.assertEqual(bts.recurrence, 1)
        self.assertEqual(BankTransaction.objects.count(), 0)

    def test_clone_scheduler_save_fail(self):
        bts = BankTransactionSchedulerFactory(
            date=datetime.date(2015, 1, 31),
            last_action=None,
            state=BankTransactionScheduler.STATE_WAITING,
            recurrence=2,
        )
        with patch.object(BankTransactionScheduler, 'save', side_effect=Exception('Boom')):
            with self.assertLogs(logger='mymoney.errors', level='ERROR'):
                bts.clone()

        bts.refresh_from_db()
        self.assertEqual(bts.date, datetime.date(2015, 1, 31))
        self.assertIsNone(bts.last_action)
        self.assertEqual(bts.state, BankTransactionScheduler.STATE_FAILED)
        self.assertEqual(bts.recurrence, 2)
        self.assertEqual(BankTransaction.objects.count(), 0)

    @patch.object(BankTransactionScheduler, 'delete', side_effect=Exception('Boom'))
    @patch.object(QuerySet, 'update', side_effect=Exception('Boom'))
    def test_clone_except_fail(self, mock_update, mock_delete):
        bts = BankTransactionSchedulerFactory(
            recurrence=1,
            state=BankTransactionScheduler.STATE_WAITING,
            date=datetime.date(2015, 1, 31),
            last_action=None,
        )
        with self.assertLogs(logger='mymoney.errors', level='ERROR'):
            bts.clone()
        bts.refresh_from_db()
        self.assertEqual(bts.state, BankTransactionScheduler.STATE_WAITING)
        self.assertIsNone(bts.last_action)
        self.assertEqual(bts.date, datetime.date(2015, 1, 31))
        self.assertEqual(bts.recurrence, 1)
        self.assertEqual(BankTransaction.objects.count(), 0)

    def test_force_currency(self):
        bankaccount = BankAccountFactory(currency='EUR')
        bts = BankTransactionSchedulerFactory(
            bankaccount=bankaccount,
            currency='USD',
        )
        self.assertEqual(bts.currency, 'EUR')


class BankTransactionSchedulerManagerTestCase(TestCase):

    def tearDown(self):
        BankTransactionScheduler.objects.all().delete()

    def test_awaiting_banktransactions_state_waiting(self):
        bts = BankTransactionSchedulerFactory(
            state=BankTransactionScheduler.STATE_WAITING,
        )
        qs = BankTransactionScheduler.objects.get_awaiting_banktransactions()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), bts)

    def test_awaiting_banktransactions_state_failed(self):
        BankTransactionSchedulerFactory(
            state=BankTransactionScheduler.STATE_FAILED,
        )
        qs = BankTransactionScheduler.objects.get_awaiting_banktransactions()
        self.assertEqual(qs.count(), 0)

    @patch('mymoney.api.banktransactionschedulers.models.timezone.now')
    def test_awaiting_banktransactions_monthly(self, mock_now):
        mock_now.return_value = datetime.datetime(
            2015, 11, 1, 0, 0, 0, 0, tzinfo=timezone.utc)

        bts = BankTransactionSchedulerFactory(
            last_action=timezone.make_aware(datetime.datetime(2015, 10, 31)),
            type=BankTransactionScheduler.TYPE_MONTHLY,
            state=BankTransactionScheduler.STATE_FINISHED,
        )
        BankTransactionSchedulerFactory(
            last_action=timezone.make_aware(datetime.datetime(2015, 11, 1)),
            type=BankTransactionScheduler.TYPE_MONTHLY,
            state=BankTransactionScheduler.STATE_FINISHED,
        )

        qs = BankTransactionScheduler.objects.get_awaiting_banktransactions()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), bts)

    @patch('mymoney.api.banktransactionschedulers.models.timezone.now')
    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_awaiting_banktransactions_weekly(self, mock_now):
        mock_now.return_value = datetime.datetime(
            2015, 11, 2, 0, 0, 0, 0, tzinfo=timezone.utc)

        bts = BankTransactionSchedulerFactory(
            last_action=timezone.make_aware(datetime.datetime(2015, 11, 1)),
            type=BankTransactionScheduler.TYPE_WEEKLY,
            state=BankTransactionScheduler.STATE_FINISHED,
        )
        BankTransactionSchedulerFactory(
            last_action=timezone.make_aware(datetime.datetime(2015, 11, 2)),
            type=BankTransactionScheduler.TYPE_WEEKLY,
            state=BankTransactionScheduler.STATE_FINISHED,
        )

        qs = BankTransactionScheduler.objects.get_awaiting_banktransactions()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), bts)

    @patch('mymoney.api.banktransactionschedulers.models.timezone.now')
    def test_awaiting_banktransactions_monthly_and_weekly(self, mock_now):
        mock_now.return_value = datetime.datetime(
            2015, 11, 2, 0, 0, 0, 0, tzinfo=timezone.utc)

        bts1 = BankTransactionSchedulerFactory(
            last_action=timezone.make_aware(datetime.datetime(2015, 10, 31)),
            type=BankTransactionScheduler.TYPE_WEEKLY,
            state=BankTransactionScheduler.STATE_FINISHED,
        )
        BankTransactionSchedulerFactory(
            last_action=timezone.make_aware(datetime.datetime(2015, 11, 2)),
            type=BankTransactionScheduler.TYPE_WEEKLY,
            state=BankTransactionScheduler.STATE_FINISHED,
        )
        bts2 = BankTransactionSchedulerFactory(
            last_action=timezone.make_aware(datetime.datetime(2015, 10, 31)),
            type=BankTransactionScheduler.TYPE_MONTHLY,
            state=BankTransactionScheduler.STATE_FINISHED,
        )
        BankTransactionSchedulerFactory(
            last_action=timezone.make_aware(datetime.datetime(2015, 11, 1)),
            type=BankTransactionScheduler.TYPE_MONTHLY,
            state=BankTransactionScheduler.STATE_FINISHED,
        )

        qs = BankTransactionScheduler.objects.get_awaiting_banktransactions()
        self.assertEqual(qs.count(), 2)
        self.assertEqual(qs[0], bts1)
        self.assertEqual(qs[1], bts2)

    def test_total_debit_none(self):
        bankaccount = BankAccountFactory()
        self.assertDictEqual(
            BankTransactionScheduler.objects.get_total_debit(bankaccount), {})

    def test_total_debit_monthly_other_bankaccount(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=-10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            amount=-10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
            bankaccount=bankaccount,
        )
        result = BankTransactionScheduler.objects.get_total_debit(bankaccount)
        self.assertEqual(result['monthly'], -10)

    def test_total_debit_monthly_with_some_credit(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=-10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            amount=10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        result = BankTransactionScheduler.objects.get_total_debit(bankaccount)
        self.assertEqual(result['monthly'], -10)

    def test_total_debit_monthly_inactive(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=-10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            amount=-10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
            status=BankTransactionScheduler.STATUS_INACTIVE,
        )
        result = BankTransactionScheduler.objects.get_total_debit(bankaccount)
        self.assertEqual(result['monthly'], -10)

    def test_total_debit_monthly_sum(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=-10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            amount=-10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        result = BankTransactionScheduler.objects.get_total_debit(bankaccount)
        self.assertEqual(result['monthly'], -20)

    def test_total_debit_weekly_other_bankaccount(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=-10,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            amount=-10,
            type=BankTransactionScheduler.TYPE_WEEKLY,
            bankaccount=bankaccount,
        )
        result = BankTransactionScheduler.objects.get_total_debit(bankaccount)
        self.assertEqual(result['weekly'], -10)

    def test_total_debit_weekly_with_some_credit(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=-10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            amount=10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        result = BankTransactionScheduler.objects.get_total_debit(bankaccount)
        self.assertEqual(result['weekly'], -10)

    def test_total_debit_weekly_inactive(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=-10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            amount=-10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_WEEKLY,
            status=BankTransactionScheduler.STATUS_INACTIVE,
        )
        result = BankTransactionScheduler.objects.get_total_debit(bankaccount)
        self.assertEqual(result['weekly'], -10)

    def test_total_debit_weekly_sum(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=-10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            amount=-10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        result = BankTransactionScheduler.objects.get_total_debit(bankaccount)
        self.assertEqual(result['weekly'], -20)

    def test_total_debit_sum(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=-10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            amount=-10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            amount=-15,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            amount=-15,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        result = BankTransactionScheduler.objects.get_total_debit(bankaccount)
        self.assertEqual(result['monthly'], -20)
        self.assertEqual(result['weekly'], -30)

    def test_total_credit_none(self):
        bankaccount = BankAccountFactory()
        self.assertDictEqual(
            BankTransactionScheduler.objects.get_total_credit(bankaccount), {})

    def test_total_credit_monthly_other_bankaccount(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            amount=10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
            bankaccount=bankaccount,
        )
        result = BankTransactionScheduler.objects.get_total_credit(bankaccount)
        self.assertEqual(result['monthly'], 10)

    def test_total_credit_monthly_with_some_debit(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            amount=-10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        result = BankTransactionScheduler.objects.get_total_credit(bankaccount)
        self.assertEqual(result['monthly'], 10)

    def test_total_credit_monthly_inactive(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            amount=10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
            status=BankTransactionScheduler.STATUS_INACTIVE,
        )
        result = BankTransactionScheduler.objects.get_total_credit(bankaccount)
        self.assertEqual(result['monthly'], 10)

    def test_total_credit_monthly_sum(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            amount=10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        result = BankTransactionScheduler.objects.get_total_credit(bankaccount)
        self.assertEqual(result['monthly'], 20)

    def test_total_credit_weekly_other_bankaccount(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=10,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            amount=10,
            type=BankTransactionScheduler.TYPE_WEEKLY,
            bankaccount=bankaccount,
        )
        result = BankTransactionScheduler.objects.get_total_credit(bankaccount)
        self.assertEqual(result['weekly'], 10)

    def test_total_credit_weekly_with_some_debit(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            amount=-10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        result = BankTransactionScheduler.objects.get_total_credit(bankaccount)
        self.assertEqual(result['weekly'], 10)

    def test_total_credit_weekly_inactive(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            amount=10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_WEEKLY,
            status=BankTransactionScheduler.STATUS_INACTIVE,
        )
        result = BankTransactionScheduler.objects.get_total_credit(bankaccount)
        self.assertEqual(result['weekly'], 10)

    def test_total_credit_weekly_sum(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            amount=10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        result = BankTransactionScheduler.objects.get_total_credit(bankaccount)
        self.assertEqual(result['weekly'], 20)

    def test_total_credit_sum(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            amount=10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            amount=10,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            amount=15,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            amount=15,
            bankaccount=bankaccount,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        result = BankTransactionScheduler.objects.get_total_credit(bankaccount)
        self.assertEqual(result['monthly'], 20)
        self.assertEqual(result['weekly'], 30)


class RelationshipTestCase(TestCase):

    def test_delete_bankaccount(self):

        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory.create_batch(5)

        bankaccount_pk = bankaccount.pk
        bankaccount.delete()

        self.assertEqual(
            BankTransactionScheduler.objects.filter(bankaccount__pk=bankaccount_pk).count(),
            0,
        )
