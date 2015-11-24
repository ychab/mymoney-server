import django_filters
from django_filters.filterset import STRICTNESS
from rest_framework.filters import DjangoFilterBackend

from mymoney.api.banktransactiontags.models import BankTransactionTag

from .forms import BankTransactionFilterForm
from .models import BankTransaction


class BankTransactionFilterBackend(DjangoFilterBackend):

    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view, queryset)
        return filter_class(
            request.query_params, queryset=queryset, request=request).qs


class BankTransactionFilter(django_filters.FilterSet):

    date = django_filters.DateFromToRangeFilter()
    amount = django_filters.RangeFilter()
    tag = django_filters.ModelMultipleChoiceFilter(
        queryset=BankTransactionTag.objects.none())

    strict = STRICTNESS.RAISE_VALIDATION_ERROR

    class Meta:
        model = BankTransaction
        form = BankTransactionFilterForm
        fields = ['date', 'amount', 'status', 'reconciled', 'tag']

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super(BankTransactionFilter, self).__init__(*args, **kwargs)
        self.filters['tag'].extra['queryset'] = \
            BankTransactionTag.objects.get_user_tags_queryset(request.user)
