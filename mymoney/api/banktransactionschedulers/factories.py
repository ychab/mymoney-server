from django.utils import timezone

from dateutil.relativedelta import relativedelta
from factory import fuzzy

from mymoney.api.banktransactions.factories import \
    AbstractBankTransactionFactory

from .models import BankTransactionScheduler


class BankTransactionSchedulerFactory(AbstractBankTransactionFactory):

    class Meta:
        model = BankTransactionScheduler

    type = fuzzy.FuzzyChoice(dict(BankTransactionScheduler.TYPES).keys())
    recurrence = fuzzy.FuzzyInteger(2, 10)
    last_action = fuzzy.FuzzyDateTime(
        start_dt=timezone.now() - relativedelta(months=2),
    )
    state = fuzzy.FuzzyChoice(dict(BankTransactionScheduler.STATES).keys())

    @classmethod
    def _prepare(cls, create, **kwargs):
        obj = super(BankTransactionSchedulerFactory, cls)._prepare(create, **kwargs)

        if obj.state == BankTransactionScheduler.STATE_WAITING:
            obj.last_action = None

        return obj
