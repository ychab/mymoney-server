import factory
from factory import fuzzy

from mymoney.api.users.factories import UserFactory

from .models import BankTransactionTag

BankTransactionTagFactory = factory.make_factory(
    BankTransactionTag,
    FACTORY_CLASS=factory.DjangoModelFactory,
    name=fuzzy.FuzzyText(),
    owner=factory.SubFactory(UserFactory),
)
