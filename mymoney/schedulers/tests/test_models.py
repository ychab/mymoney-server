import datetime
from decimal import Decimal
from unittest.mock import patch

from django.db.models import QuerySet
from django.test import TestCase, override_settings
from django.utils import timezone

from mymoney.accounts.factories import AccountFactory
from mymoney.transactions.models import Transaction
from mymoney.tags.factories import TagFactory

from ..factories import SchedulerFactory
from ..models import Scheduler


class SchedulerModelTestCase(TestCase):

    def tearDown(self):
        Transaction.objects.all().delete()

    def test_clone_field_date_weekly(self):
        scheduler = SchedulerFactory(
            date=datetime.date(2015, 3, 26),
            type=Scheduler.TYPE_WEEKLY,
        )
        scheduler.clone()
        self.assertEqual(Transaction.objects.count(), 1)
        bt_clone = Transaction.objects.first()
        self.assertEqual(bt_clone.date, datetime.date(2015, 4, 2))

    def test_clone_field_date_monthly(self):
        scheduler = SchedulerFactory(
            date=datetime.date(2015, 1, 31),
            type=Scheduler.TYPE_MONTHLY,
        )
        scheduler.clone()
        self.assertEqual(Transaction.objects.count(), 1)
        bt_clone = Transaction.objects.first()
        self.assertEqual(bt_clone.date, datetime.date(2015, 2, 28))

    def test_clone_field_currency(self):
        account = AccountFactory(balance=0, currency='EUR')
        scheduler = SchedulerFactory(account=account)
        scheduler.clone()
        self.assertEqual(Transaction.objects.count(), 1)
        bt_clone = Transaction.objects.first()
        self.assertEqual(bt_clone.currency, scheduler.currency)
        self.assertEqual(bt_clone.currency, account.currency)

    def test_clone_field_reconciled(self):
        scheduler = SchedulerFactory(reconciled=True)
        scheduler.clone()
        self.assertEqual(Transaction.objects.count(), 1)
        bt_clone = Transaction.objects.first()
        self.assertFalse(bt_clone.reconciled)

    def test_clone_field_scheduled(self):
        scheduler = SchedulerFactory()
        scheduler.clone()
        self.assertEqual(Transaction.objects.count(), 1)
        bt_clone = Transaction.objects.first()
        self.assertTrue(bt_clone.scheduled)

    def test_clone_fields(self):
        account = AccountFactory()
        scheduler = SchedulerFactory(
            label="foo",
            account=account,
            amount=Decimal('10.23'),
            status=Transaction.STATUS_ACTIVE,
            reconciled=True,
            payment_method=Transaction.PAYMENT_METHOD_CASH,
            memo="Test",
            tag=TagFactory(),
        )
        scheduler.clone()
        self.assertEqual(Transaction.objects.count(), 1)
        bt_clone = Transaction.objects.first()
        self.assertEqual(bt_clone.label, scheduler.label)
        self.assertEqual(bt_clone.account, scheduler.account)
        self.assertEqual(bt_clone.amount, scheduler.amount)
        self.assertEqual(bt_clone.status, scheduler.status)
        self.assertEqual(bt_clone.payment_method, scheduler.payment_method)
        self.assertEqual(bt_clone.memo, scheduler.memo)
        self.assertEqual(bt_clone.tag.pk, scheduler.tag.pk)

    def test_account_balance(self):
        account = AccountFactory(balance=0)
        scheduler = SchedulerFactory(
            account=account,
            amount=10,
            status=Scheduler.STATUS_ACTIVE,
        )
        scheduler.clone()
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal(10))

    def test_clone_recurrence_decrement(self):
        scheduler = SchedulerFactory(recurrence=2)
        scheduler.clone()
        scheduler.refresh_from_db()
        self.assertEqual(scheduler.recurrence, 1)

    def test_clone_recurrence_infinite(self):
        scheduler = SchedulerFactory(recurrence=None)
        scheduler.clone()
        scheduler.refresh_from_db()
        self.assertIsNone(scheduler.recurrence)

    def test_clone_scheduler_delete(self):
        scheduler = SchedulerFactory(recurrence=1)
        scheduler.clone()
        with self.assertRaises(Scheduler.DoesNotExist):
            scheduler.refresh_from_db()

    def test_clone_scheduler_date_monthly(self):
        scheduler = SchedulerFactory(
            date=datetime.date(2015, 1, 31),
            type=Scheduler.TYPE_MONTHLY,
        )
        scheduler.clone()
        scheduler.refresh_from_db()
        self.assertEqual(scheduler.date, datetime.date(2015, 2, 28))

    def test_clone_scheduler_date_weekly(self):
        scheduler = SchedulerFactory(
            date=datetime.date(2015, 3, 26),
            type=Scheduler.TYPE_WEEKLY,
        )
        scheduler.clone()
        scheduler.refresh_from_db()
        self.assertEqual(scheduler.date, datetime.date(2015, 4, 2))

    @patch('mymoney.schedulers.models.timezone.now')
    def test_clone_scheduler_last_action(self, mock_now):
        dtime = datetime.datetime(2015, 10, 31, 0, 0, 0, 0, tzinfo=timezone.utc)
        mock_now.return_value = dtime
        scheduler = SchedulerFactory(
            last_action=None,
        )
        scheduler.clone()
        scheduler.refresh_from_db()
        self.assertEqual(scheduler.last_action, dtime)

    def test_clone_scheduler_state(self):
        scheduler = SchedulerFactory(
            state=Scheduler.STATE_WAITING,
        )
        scheduler.clone()
        scheduler.refresh_from_db()
        self.assertEqual(scheduler.state, Scheduler.STATE_FINISHED)

    @patch(
        'mymoney.schedulers.models.Transaction.objects.create',
        side_effect=Exception('Boom'),
    )
    def test_clone_banktransaction_create_fail(self, mock_method):
        scheduler = SchedulerFactory(
            state=Scheduler.STATE_WAITING,
        )
        with self.assertLogs(logger='mymoney.errors', level='ERROR'):
            scheduler.clone()
        scheduler.refresh_from_db()
        self.assertEqual(scheduler.state, Scheduler.STATE_FAILED)

    @patch.object(Scheduler, 'delete', side_effect=Exception('Boom'))
    def test_clone_scheduler_delete_fail(self, mock_method):
        scheduler = SchedulerFactory(
            recurrence=1,
            state=Scheduler.STATE_WAITING,
        )
        with self.assertLogs(logger='mymoney.errors', level='ERROR'):
            scheduler.clone()
        scheduler.refresh_from_db()
        self.assertEqual(scheduler.state, Scheduler.STATE_FAILED)
        self.assertEqual(scheduler.recurrence, 1)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_clone_scheduler_save_fail(self):
        scheduler = SchedulerFactory(
            date=datetime.date(2015, 1, 31),
            last_action=None,
            state=Scheduler.STATE_WAITING,
            recurrence=2,
        )
        with patch.object(Scheduler, 'save', side_effect=Exception('Boom')):
            with self.assertLogs(logger='mymoney.errors', level='ERROR'):
                scheduler.clone()

        scheduler.refresh_from_db()
        self.assertEqual(scheduler.date, datetime.date(2015, 1, 31))
        self.assertIsNone(scheduler.last_action)
        self.assertEqual(scheduler.state, Scheduler.STATE_FAILED)
        self.assertEqual(scheduler.recurrence, 2)
        self.assertEqual(Transaction.objects.count(), 0)

    @patch.object(Scheduler, 'delete', side_effect=Exception('Boom'))
    @patch.object(QuerySet, 'update', side_effect=Exception('Boom'))
    def test_clone_except_fail(self, mock_update, mock_delete):
        scheduler = SchedulerFactory(
            recurrence=1,
            state=Scheduler.STATE_WAITING,
            date=datetime.date(2015, 1, 31),
            last_action=None,
        )
        with self.assertLogs(logger='mymoney.errors', level='ERROR'):
            scheduler.clone()
        scheduler.refresh_from_db()
        self.assertEqual(scheduler.state, Scheduler.STATE_WAITING)
        self.assertIsNone(scheduler.last_action)
        self.assertEqual(scheduler.date, datetime.date(2015, 1, 31))
        self.assertEqual(scheduler.recurrence, 1)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_force_currency(self):
        account = AccountFactory(currency='EUR')
        scheduler = SchedulerFactory(
            account=account,
            currency='USD',
        )
        self.assertEqual(scheduler.currency, 'EUR')


class SchedulerManagerTestCase(TestCase):

    def tearDown(self):
        Scheduler.objects.all().delete()

    def test_awaiting_transactions_state_waiting(self):
        scheduler = SchedulerFactory(
            state=Scheduler.STATE_WAITING,
        )
        qs = Scheduler.objects.get_awaiting_transactions()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), scheduler)

    def test_awaiting_transactions_state_failed(self):
        SchedulerFactory(
            state=Scheduler.STATE_FAILED,
        )
        qs = Scheduler.objects.get_awaiting_transactions()
        self.assertEqual(qs.count(), 0)

    @patch('mymoney.schedulers.models.timezone.now')
    def test_awaiting_transactions_monthly(self, mock_now):
        mock_now.return_value = datetime.datetime(
            2015, 11, 1, 0, 0, 0, 0, tzinfo=timezone.utc)

        scheduler = SchedulerFactory(
            last_action=timezone.make_aware(datetime.datetime(2015, 10, 31)),
            type=Scheduler.TYPE_MONTHLY,
            state=Scheduler.STATE_FINISHED,
        )
        SchedulerFactory(
            last_action=timezone.make_aware(datetime.datetime(2015, 11, 1)),
            type=Scheduler.TYPE_MONTHLY,
            state=Scheduler.STATE_FINISHED,
        )

        qs = Scheduler.objects.get_awaiting_transactions()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), scheduler)

    @patch('mymoney.schedulers.models.timezone.now')
    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_awaiting_transactions_weekly(self, mock_now):
        mock_now.return_value = datetime.datetime(
            2015, 11, 2, 0, 0, 0, 0, tzinfo=timezone.utc)

        scheduler = SchedulerFactory(
            last_action=timezone.make_aware(datetime.datetime(2015, 11, 1)),
            type=Scheduler.TYPE_WEEKLY,
            state=Scheduler.STATE_FINISHED,
        )
        SchedulerFactory(
            last_action=timezone.make_aware(datetime.datetime(2015, 11, 2)),
            type=Scheduler.TYPE_WEEKLY,
            state=Scheduler.STATE_FINISHED,
        )

        qs = Scheduler.objects.get_awaiting_transactions()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), scheduler)

    @patch('mymoney.schedulers.models.timezone.now')
    def test_awaiting_transactions_monthly_and_weekly(self, mock_now):
        mock_now.return_value = datetime.datetime(
            2015, 11, 2, 0, 0, 0, 0, tzinfo=timezone.utc)

        bts1 = SchedulerFactory(
            last_action=timezone.make_aware(datetime.datetime(2015, 10, 31)),
            type=Scheduler.TYPE_WEEKLY,
            state=Scheduler.STATE_FINISHED,
        )
        SchedulerFactory(
            last_action=timezone.make_aware(datetime.datetime(2015, 11, 2)),
            type=Scheduler.TYPE_WEEKLY,
            state=Scheduler.STATE_FINISHED,
        )
        bts2 = SchedulerFactory(
            last_action=timezone.make_aware(datetime.datetime(2015, 10, 31)),
            type=Scheduler.TYPE_MONTHLY,
            state=Scheduler.STATE_FINISHED,
        )
        SchedulerFactory(
            last_action=timezone.make_aware(datetime.datetime(2015, 11, 1)),
            type=Scheduler.TYPE_MONTHLY,
            state=Scheduler.STATE_FINISHED,
        )

        qs = Scheduler.objects.get_awaiting_transactions()
        self.assertEqual(qs.count(), 2)
        self.assertEqual(qs[0], bts1)
        self.assertEqual(qs[1], bts2)

    def test_total_debit_none(self):
        account = AccountFactory()
        self.assertDictEqual(
            Scheduler.objects.get_total_debit(account), {})

    def test_total_debit_monthly_other_account(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=-10,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            amount=-10,
            type=Scheduler.TYPE_MONTHLY,
            account=account,
        )
        result = Scheduler.objects.get_total_debit(account)
        self.assertEqual(result['monthly'], -10)

    def test_total_debit_monthly_with_some_credit(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=-10,
            account=account,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            amount=10,
            account=account,
            type=Scheduler.TYPE_MONTHLY,
        )
        result = Scheduler.objects.get_total_debit(account)
        self.assertEqual(result['monthly'], -10)

    def test_total_debit_monthly_inactive(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=-10,
            account=account,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            amount=-10,
            account=account,
            type=Scheduler.TYPE_MONTHLY,
            status=Scheduler.STATUS_INACTIVE,
        )
        result = Scheduler.objects.get_total_debit(account)
        self.assertEqual(result['monthly'], -10)

    def test_total_debit_monthly_sum(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=-10,
            account=account,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            amount=-10,
            account=account,
            type=Scheduler.TYPE_MONTHLY,
        )
        result = Scheduler.objects.get_total_debit(account)
        self.assertEqual(result['monthly'], -20)

    def test_total_debit_weekly_other_account(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=-10,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            amount=-10,
            type=Scheduler.TYPE_WEEKLY,
            account=account,
        )
        result = Scheduler.objects.get_total_debit(account)
        self.assertEqual(result['weekly'], -10)

    def test_total_debit_weekly_with_some_credit(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=-10,
            account=account,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            amount=10,
            account=account,
            type=Scheduler.TYPE_WEEKLY,
        )
        result = Scheduler.objects.get_total_debit(account)
        self.assertEqual(result['weekly'], -10)

    def test_total_debit_weekly_inactive(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=-10,
            account=account,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            amount=-10,
            account=account,
            type=Scheduler.TYPE_WEEKLY,
            status=Scheduler.STATUS_INACTIVE,
        )
        result = Scheduler.objects.get_total_debit(account)
        self.assertEqual(result['weekly'], -10)

    def test_total_debit_weekly_sum(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=-10,
            account=account,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            amount=-10,
            account=account,
            type=Scheduler.TYPE_WEEKLY,
        )
        result = Scheduler.objects.get_total_debit(account)
        self.assertEqual(result['weekly'], -20)

    def test_total_debit_sum(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=-10,
            account=account,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            amount=-10,
            account=account,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            amount=-15,
            account=account,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            amount=-15,
            account=account,
            type=Scheduler.TYPE_WEEKLY,
        )
        result = Scheduler.objects.get_total_debit(account)
        self.assertEqual(result['monthly'], -20)
        self.assertEqual(result['weekly'], -30)

    def test_total_credit_none(self):
        account = AccountFactory()
        self.assertDictEqual(
            Scheduler.objects.get_total_credit(account), {})

    def test_total_credit_monthly_other_account(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=10,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            amount=10,
            type=Scheduler.TYPE_MONTHLY,
            account=account,
        )
        result = Scheduler.objects.get_total_credit(account)
        self.assertEqual(result['monthly'], 10)

    def test_total_credit_monthly_with_some_debit(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=10,
            account=account,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            amount=-10,
            account=account,
            type=Scheduler.TYPE_MONTHLY,
        )
        result = Scheduler.objects.get_total_credit(account)
        self.assertEqual(result['monthly'], 10)

    def test_total_credit_monthly_inactive(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=10,
            account=account,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            amount=10,
            account=account,
            type=Scheduler.TYPE_MONTHLY,
            status=Scheduler.STATUS_INACTIVE,
        )
        result = Scheduler.objects.get_total_credit(account)
        self.assertEqual(result['monthly'], 10)

    def test_total_credit_monthly_sum(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=10,
            account=account,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            amount=10,
            account=account,
            type=Scheduler.TYPE_MONTHLY,
        )
        result = Scheduler.objects.get_total_credit(account)
        self.assertEqual(result['monthly'], 20)

    def test_total_credit_weekly_other_account(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=10,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            amount=10,
            type=Scheduler.TYPE_WEEKLY,
            account=account,
        )
        result = Scheduler.objects.get_total_credit(account)
        self.assertEqual(result['weekly'], 10)

    def test_total_credit_weekly_with_some_debit(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=10,
            account=account,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            amount=-10,
            account=account,
            type=Scheduler.TYPE_WEEKLY,
        )
        result = Scheduler.objects.get_total_credit(account)
        self.assertEqual(result['weekly'], 10)

    def test_total_credit_weekly_inactive(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=10,
            account=account,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            amount=10,
            account=account,
            type=Scheduler.TYPE_WEEKLY,
            status=Scheduler.STATUS_INACTIVE,
        )
        result = Scheduler.objects.get_total_credit(account)
        self.assertEqual(result['weekly'], 10)

    def test_total_credit_weekly_sum(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=10,
            account=account,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            amount=10,
            account=account,
            type=Scheduler.TYPE_WEEKLY,
        )
        result = Scheduler.objects.get_total_credit(account)
        self.assertEqual(result['weekly'], 20)

    def test_total_credit_sum(self):
        account = AccountFactory()
        SchedulerFactory(
            amount=10,
            account=account,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            amount=10,
            account=account,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            amount=15,
            account=account,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            amount=15,
            account=account,
            type=Scheduler.TYPE_WEEKLY,
        )
        result = Scheduler.objects.get_total_credit(account)
        self.assertEqual(result['monthly'], 20)
        self.assertEqual(result['weekly'], 30)


class RelationshipTestCase(TestCase):

    def test_delete_account(self):

        account = AccountFactory()
        SchedulerFactory.create_batch(5)

        account_pk = account.pk
        account.delete()

        self.assertEqual(
            Scheduler.objects.filter(account__pk=account_pk).count(),
            0,
        )
