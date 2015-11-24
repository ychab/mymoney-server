from django.db.models import Count, Max, Min, Sum
from django.utils.functional import cached_property

from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from mymoney.api.bankaccounts.mixins import BankAccountContext
from mymoney.api.banktransactions.models import BankTransaction
from mymoney.api.banktransactions.serializers import (
    BankTransactionDetailSerializer, BankTransactionTeaserSerializer,
)
from mymoney.core.iterators import DateIterator
from mymoney.core.paginators import DatePaginator
from mymoney.core.utils.dates import get_date_ranges

from .serializers import (
    RatioInputSerializer, RatioOutputSerializer, RatioSummaryInputSerializer,
    TrendTimeInputSerializer, TrendTimeOuputSerializer,
)


class RatioAnalyticsViewSet(BankAccountContext, GenericViewSet):

    def __init__(self, *args, **kwargs):
        super(RatioAnalyticsViewSet, self).__init__(*args, **kwargs)
        self.filters = []

    def list(self, request, *args, **kwargs):
        serializer = RatioInputSerializer(
            data=request.query_params, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.filters = serializer.validated_data

        instances, subtotal = [], 0
        total = self.total_queryset

        if total is not None:
            for data in self.tag_queryset:
                instances.append({
                    'tag': data['tag'],
                    'sum': data['sum'],
                    'count': data['count'],
                    'percentage': round(data['sum'] * 100 / total, 2),
                })
                subtotal += data['sum']

        return Response({
            'results': RatioOutputSerializer(instances, many=True).data,
            'subtotal': subtotal,
            'total': total,
        })

    @list_route(['get'])
    def summary(self, request, *args, **kwargs):
        serializer = RatioSummaryInputSerializer(
            data=request.query_params, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.filters = serializer.validated_data

        qs = self.base_queryset

        if serializer.data['tag'] is not None:
            qs = qs.filter(tag__pk=serializer.data['tag'])
        else:
            qs = qs.filter(tag__isnull=True)

        qs = qs.order_by('date', 'id')

        instances, total = [], 0
        for banktransaction in qs:
            instances.append(banktransaction)
            total += banktransaction.amount

        return Response({
            'results': BankTransactionTeaserSerializer(instances, many=True).data,
            'total': total,
        })

    @property
    def base_queryset(self):

        qs = BankTransaction.objects.filter(
            bankaccount=self.bankaccount,
            status=BankTransaction.STATUS_ACTIVE,
            date__range=(self.filters['date_start'], self.filters['date_end']),
        )

        if self.filters['type'] == RatioInputSerializer.SINGLE_DEBIT:
            qs = qs.filter(amount__lt=0)
        elif self.filters['type'] == RatioInputSerializer.SINGLE_CREDIT:
            qs = qs.filter(amount__gt=0)

        if 'reconciled' in self.filters:
            qs = qs.filter(reconciled=self.filters['reconciled'])

        return qs

    @cached_property
    def queryset(self):
        qs = self.base_queryset

        if self.filters['type'] in (RatioInputSerializer.SUM_CREDIT, RatioInputSerializer.SUM_DEBIT):
            qs = qs.values('tag')
            qs = qs.annotate(sum=Sum('amount'))

            if self.filters['type'] == RatioInputSerializer.SUM_CREDIT:
                qs = qs.filter(sum__gt=0)
            else:
                qs = qs.filter(sum__lt=0)

        return qs

    @property
    def total_queryset(self):

        if self.filters['type'] in (RatioInputSerializer.SINGLE_CREDIT, RatioInputSerializer.SINGLE_DEBIT):
            field = 'amount'
        else:
            field = 'sum'

        return self.queryset.aggregate(total=Sum(field))['total']

    @property
    def tag_queryset(self):
        qs = self.queryset

        if self.filters['tags']:
            qs = qs.filter(tag__in=self.filters['tags'])

        if self.filters['type'] in (RatioInputSerializer.SINGLE_CREDIT, RatioInputSerializer.SINGLE_DEBIT):
            qs = qs.values('tag')
            qs = qs.annotate(sum=Sum('amount'))

        qs = qs.annotate(count=Count('id'))

        if 'sum_min' in self.filters and 'sum_max' in self.filters:
            qs = qs.filter(sum__range=(
                self.filters['sum_min'],
                self.filters['sum_max'],
            ))
        elif 'sum_min' in self.filters:
            qs = qs.filter(sum__gte=self.filters['sum_min'])
        elif 'sum_max' in self.filters:
            qs = qs.filter(sum__lte=self.filters['sum_max'])

        if self.filters['type'] in (RatioInputSerializer.SINGLE_DEBIT, RatioInputSerializer.SUM_DEBIT):
            qs = qs.order_by('sum')
        else:
            qs = qs.order_by('-sum')

        return qs


class TrendTimeAnalyticsViewSet(BankAccountContext, GenericViewSet):

    def __init__(self, *args, **kwargs):
        super(TrendTimeAnalyticsViewSet, self).__init__(*args, **kwargs)
        self.filters = []

    def list(self, request, *args, **kwargs):
        serializer = TrendTimeInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        self.filters = serializer.validated_data

        results, links = [], {}

        # Get first and last bank transaction to prevent infinite pager. If
        # one is missing, it just mean that there is no data at all.
        first, last = self.get_queryset_dates_delimiters()
        if first and last:
            base_date = self.filters['date']
            granularity = self.filters['granularity']

            # Requested date is out of range?
            first_range = get_date_ranges(first, granularity)[0]
            last_range = get_date_ranges(last, granularity)[1]
            if first_range <= base_date <= last_range:

                date_start, date_end = get_date_ranges(
                    base_date,
                    granularity,
                )

                balance = self.get_queryset_balance(date_start)['sum'] or 0
                balance += self.bankaccount.balance_initial

                items_qs = self.get_queryset_items(date_start, date_end)
                items = {item['date']: item for item in items_qs}

                # Start and end iterator at first/last bank transaction,
                # not the range calculated.
                iterator = DateIterator(
                    first if first > date_start else date_start,
                    last if last < date_end else date_end,
                )
                instances = []
                for date_step in iterator:
                    delta = percentage = count = 0

                    # If no new bank transaction, same as previous.
                    if date_step in items:
                        delta = items[date_step]['sum']
                        percentage = (delta * 100 / balance) if balance else 0
                        balance += items[date_step]['sum']
                        count = items[date_step]['count']

                    instances.append({
                        'date': date_step,
                        'count': count,
                        'delta': delta,
                        'balance': balance,
                        'percentage': percentage,
                    })

                results = TrendTimeOuputSerializer(instances, many=True).data
                paginator = DatePaginator(first_range, last_range, granularity)
                links = paginator.get_links(base_date, request)

        return Response({
            'results': results,
            'previous': links.get('previous'),
            'next': links.get('next'),
        })

    @list_route(['get'])
    def summary(self, request, *args, **kwargs):
        serializer = TrendTimeInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        self.filters = serializer.validated_data

        qs = (
            self.base_queryset
            .filter(date=serializer.data['date'])
            .select_related('tag')
            .order_by('pk')
        )

        total = 0
        for banktransaction in qs:
            total += banktransaction.amount

        return Response({
            'results': BankTransactionDetailSerializer(qs, many=True).data,
            'total': total,
        })

    @cached_property
    def base_queryset(self):

        qs = BankTransaction.objects.filter(
            bankaccount=self.bankaccount,
            status=BankTransaction.STATUS_ACTIVE,
        )

        if 'reconciled' in self.filters:
            qs = qs.filter(reconciled=self.filters['reconciled'])

        return qs

    def get_queryset_dates_delimiters(self):

        dates = self.base_queryset.aggregate(
            first=Min('date'),
            last=Max('date'),
        )
        return dates['first'], dates['last']

    def get_queryset_balance(self, date_start):

        qs = self.base_queryset.filter(
            date__lt=date_start,
        ).aggregate(
            sum=Sum('amount')
        )

        return qs

    def get_queryset_items(self, date_start, date_end):

        qs = self.base_queryset.filter(
            date__range=(date_start, date_end),
        )

        qs = qs.values('date')
        qs = qs.annotate(sum=Sum('amount'), count=Count('id'))
        qs = qs.order_by('date')

        return qs
