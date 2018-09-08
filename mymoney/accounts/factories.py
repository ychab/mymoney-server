import factory
from factory import fuzzy

from mymoney.core.utils.currencies import get_currencies

from .models import Account


class AccountFactory(factory.DjangoModelFactory):

    class Meta:
        model = Account

    label = factory.Sequence(lambda n: 'test_%d' % n)
    balance = fuzzy.FuzzyDecimal(-10000, 10000, precision=2)
    currency = fuzzy.FuzzyChoice(dict(get_currencies()).keys())
