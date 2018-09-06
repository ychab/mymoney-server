import django_filters
from django_filters import rest_framework as filters

from mymoney.tags.models import Tag

from .forms import TransactionFilterForm
from .models import Transaction


class TransactionFilter(filters.FilterSet):
    date = django_filters.DateFromToRangeFilter()
    amount = django_filters.RangeFilter()
    tag = django_filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all())

    class Meta:
        model = Transaction
        form = TransactionFilterForm
        fields = ['date', 'amount', 'status', 'reconciled', 'tag']
