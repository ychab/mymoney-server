import datetime

from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

from mymoney.bankaccounts import BankAccountFactory
from mymoney.banktransactions import BankTransaction

from ..factories import BankTransactionSchedulerFactory
from ..models import BankTransactionScheduler


class CommandTestCase(TestCase):

    def tearDown(self):
        BankTransaction.objects.all().delete()

    def test_none(self):
        out = StringIO()
        call_command('clonescheduled', stdout=out)
        self.assertEqual(BankTransaction.objects.all().count(), 0)

    def test_order(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            bankaccount=bankaccount,
            label='foo',
            state=BankTransactionScheduler.STATE_WAITING,
            date=datetime.date(2015, 10, 29),
        )
        BankTransactionSchedulerFactory(
            bankaccount=bankaccount,
            label='bar',
            state=BankTransactionScheduler.STATE_WAITING,
            date=datetime.date(2015, 10, 30),
        )
        out = StringIO()
        self.assertEqual(BankTransaction.objects.all().count(), 0)
        call_command('clonescheduled', limit=1, stdout=out)
        self.assertEqual(BankTransaction.objects.all().count(), 1)
        self.assertEqual(BankTransaction.objects.first().label, 'foo')

    def test_limit(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            bankaccount=bankaccount,
            state=BankTransactionScheduler.STATE_WAITING,
        )
        BankTransactionSchedulerFactory(
            bankaccount=bankaccount,
            state=BankTransactionScheduler.STATE_WAITING,
        )
        out = StringIO()
        self.assertEqual(BankTransaction.objects.all().count(), 0)
        call_command('clonescheduled', limit=1, stdout=out)
        self.assertEqual(BankTransaction.objects.all().count(), 1)

    def test_no_more_awaiting(self):
        bankaccount = BankAccountFactory()
        BankTransactionSchedulerFactory(
            bankaccount=bankaccount,
            state=BankTransactionScheduler.STATE_WAITING,
        )
        BankTransactionSchedulerFactory(
            bankaccount=bankaccount,
            state=BankTransactionScheduler.STATE_WAITING,
        )
        out = StringIO()

        call_command('clonescheduled', limit=1, stdout=out)
        self.assertEqual(BankTransaction.objects.all().count(), 1)

        call_command('clonescheduled', stdout=out)
        self.assertEqual(BankTransaction.objects.all().count(), 2)

        call_command('clonescheduled', stdout=out)
        self.assertEqual(BankTransaction.objects.all().count(), 2)
        self.assertIn('Scheduled bank transaction have been cloned.', out.getvalue())
