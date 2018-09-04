from django.test import TestCase
from django.utils import timezone

from ..factories import BankTransactionSchedulerFactory
from ..models import BankTransactionScheduler


class BankTransactionSchedulerFactoryTestCase(TestCase):

    def test_waiting_last_action_none(self):
        bts = BankTransactionSchedulerFactory(
            state=BankTransactionScheduler.STATE_WAITING,
            last_action=timezone.now(),
        )
        self.assertIsNone(bts.last_action)
