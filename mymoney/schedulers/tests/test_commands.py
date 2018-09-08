import datetime

from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

from mymoney.accounts.factories import AccountFactory
from mymoney.transactions.models import Transaction

from ..factories import SchedulerFactory
from ..models import Scheduler


class CommandTestCase(TestCase):

    def tearDown(self):
        Transaction.objects.all().delete()

    def test_none(self):
        out = StringIO()
        call_command('clonescheduled', stdout=out)
        self.assertEqual(Transaction.objects.all().count(), 0)

    def test_order(self):
        account = AccountFactory()
        SchedulerFactory(
            account=account,
            label='foo',
            state=Scheduler.STATE_WAITING,
            date=datetime.date(2015, 10, 29),
        )
        SchedulerFactory(
            account=account,
            label='bar',
            state=Scheduler.STATE_WAITING,
            date=datetime.date(2015, 10, 30),
        )
        out = StringIO()
        self.assertEqual(Transaction.objects.all().count(), 0)
        call_command('clonescheduled', limit=1, stdout=out)
        self.assertEqual(Transaction.objects.all().count(), 1)
        self.assertEqual(Transaction.objects.first().label, 'foo')

    def test_limit(self):
        account = AccountFactory()
        SchedulerFactory(
            account=account,
            state=Scheduler.STATE_WAITING,
        )
        SchedulerFactory(
            account=account,
            state=Scheduler.STATE_WAITING,
        )
        out = StringIO()
        self.assertEqual(Transaction.objects.all().count(), 0)
        call_command('clonescheduled', limit=1, stdout=out)
        self.assertEqual(Transaction.objects.all().count(), 1)

    def test_no_more_awaiting(self):
        account = AccountFactory()
        SchedulerFactory(
            account=account,
            state=Scheduler.STATE_WAITING,
        )
        SchedulerFactory(
            account=account,
            state=Scheduler.STATE_WAITING,
        )
        out = StringIO()

        call_command('clonescheduled', limit=1, stdout=out)
        self.assertEqual(Transaction.objects.all().count(), 1)

        call_command('clonescheduled', stdout=out)
        self.assertEqual(Transaction.objects.all().count(), 2)

        call_command('clonescheduled', stdout=out)
        self.assertEqual(Transaction.objects.all().count(), 2)
        self.assertIn('Scheduled bank transaction have been cloned.', out.getvalue())
