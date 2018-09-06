from django.utils import timezone

from dateutil.relativedelta import relativedelta
from factory import fuzzy

from mymoney.transactions.factories import AbstractTransactionFactory

from .models import Scheduler


class SchedulerFactory(AbstractTransactionFactory):

    class Meta:
        model = Scheduler

    type = fuzzy.FuzzyChoice(dict(Scheduler.TYPES).keys())
    recurrence = fuzzy.FuzzyInteger(2, 10)
    last_action = fuzzy.FuzzyDateTime(
        start_dt=timezone.now() - relativedelta(months=2),
    )
    state = fuzzy.FuzzyChoice(dict(Scheduler.STATES).keys())
