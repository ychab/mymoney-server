from django.db.models import Count, Sum
from django.utils.functional import cached_property

from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.views import APIView

from mymoney.transactions.models import Transaction
from mymoney.transactions.serializers import BankTransactionTeaserSerializer

from .serializers import (
    RatioInputSerializer, RatioOutputSerializer, RatioSummaryInputSerializer,
)


class RatioAnalyticsViewSet(APIView):

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

        qs = Transaction.objects.filter(
            bankaccount=self.bankaccount,
            status=Transaction.STATUS_ACTIVE,
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
