import factory
from factory import fuzzy

from .models import Tag

TagFactory = factory.make_factory(
    Tag,
    FACTORY_CLASS=factory.DjangoModelFactory,
    name=fuzzy.FuzzyText(),
)
