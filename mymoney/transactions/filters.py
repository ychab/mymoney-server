import django_filters
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet

from mymoney.tags.models import Tag

from .forms import TransactionFilterForm
from .models import Transaction


# class TransactionFilterBackend(DjangoFilterBackend):
#
#     def filter_queryset(self, request, queryset, view):
#         filter_class = self.get_filter_class(view, queryset)
#         return filter_class(
#             request.query_params, queryset=queryset, request=request).qs


class TransactionFilter(filters.FilterSet):
    date = django_filters.DateFromToRangeFilter()
    amount = django_filters.RangeFilter()
    tag = django_filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all())

    class Meta:
        model = Transaction
        form = TransactionFilterForm
        fields = ['date', 'amount', 'status', 'reconciled', 'tag']
