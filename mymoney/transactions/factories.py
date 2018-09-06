import datetime

import factory
from dateutil.relativedelta import relativedelta
from factory import fuzzy

from mymoney.accounts.factories import AccountFactory

from .models import Transaction


class AbstractTransactionFactory(factory.DjangoModelFactory):

    class Meta:
        abstract = True

    label = factory.Sequence(lambda n: 'test_%d' % n)
    account = factory.SubFactory(AccountFactory)
    date = fuzzy.FuzzyDate(datetime.date.today() - relativedelta(months=1))
    amount = fuzzy.FuzzyDecimal(-1000)
    currency = factory.SelfAttribute('account.currency')
    payment_method = fuzzy.FuzzyChoice(dict(Transaction.PAYMENT_METHODS).keys())


class TransactionFactory(AbstractTransactionFactory):

    class Meta:
        model = Transaction

    scheduled = False
