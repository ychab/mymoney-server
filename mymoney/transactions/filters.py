import django_filters
from django_filters.filterset import STRICTNESS
from django_filters.rest_framework import DjangoFilterBackend, FilterSet

from mymoney.banktransactiontags import BankTransactionTag

from .forms import BankTransactionFilterForm
from .models import BankTransaction


class BankTransactionFilterBackend(DjangoFilterBackend):

    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view, queryset)
        return filter_class(
            request.query_params, queryset=queryset, request=request).qs


class BankTransactionFilter(FilterSet):

    date = django_filters.DateFromToRangeFilter()
    amount = django_filters.RangeFilter()
    tag = django_filters.ModelMultipleChoiceFilter(
        queryset=BankTransactionTag.objects.none())

    class Meta:
        model = BankTransaction
        strict = STRICTNESS.RAISE_VALIDATION_ERROR
        form = BankTransactionFilterForm
        fields = ['date', 'amount', 'status', 'reconciled', 'tag']

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super(BankTransactionFilter, self).__init__(*args, **kwargs)
        self.filters['tag'].queryset = \
            BankTransactionTag.objects.get_user_tags_queryset(request.user)
