from collections import OrderedDict

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from django_filters.rest_framework import DjangoFilterBackend

from mymoney.core.utils import get_default_account
from mymoney.transactions.filters import TransactionFilter

from .models import Transaction
from .serializers import (
    TransactionDeleteMutipleSerializer, TransactionDetailSerializer,
    TransactionListSerializer, TransactionPartialUpdateMutipleSerializer,
    TransactionSerializer,
)


class TransactionViewSet(ModelViewSet):
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter,)
    filterset_class = TransactionFilter
    search_fields = ('label',)
    ordering_fields = ('label', 'date')
    ordering = ('-date',)

    def get_queryset(self):
        return Transaction.objects.filter(account=get_default_account())

    def get_serializer_class(self):
        if self.action == 'list':
            return TransactionListSerializer
        elif self.action == 'retrieve':
            return TransactionDetailSerializer
        return TransactionSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.order_by(*(queryset.query.order_by + ('-id',)))
        queryset = self._add_queryset_extra_fields(queryset)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=['patch'], detail=False, url_path='partial-update-multiple')
    def partial_update_multiple(self, request, *args, **kwargs):
        serializer = TransactionPartialUpdateMutipleSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        fields = {k: v for k, v in serializer.data.items() if k not in ('ids',)}

        transactions = Transaction.objects.filter(pk__in=serializer.data['ids'])
        for transaction in transactions:
            for field, value in fields.items():
                setattr(transaction, field, value)
            transaction.save(update_fields=fields.keys())

        return Response()

    @action(methods=['delete'], detail=False, url_path='delete-multiple')
    def delete_multiple(self, request, *args, **kwargs):
        serializer = TransactionDeleteMutipleSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        transactions = Transaction.objects.filter(pk__in=serializer.data['ids'])
        for transaction in transactions:
            transaction.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _add_queryset_extra_fields(self, qs):
        """
        Add extra fields to the queryset.
        By using SQL and not Python, we could alter order_by and sort without
        altering the new balances fields.

        Extra fields are:
        - total_balance
        - reconciled_balance
        """
        account = get_default_account()

        # Unfortunetly, we cannot get it by doing the opposite (i.e :
        # total balance - SUM(futur bt) because with postgreSQL at least,
        # the last dated bank transaction would give None :
        # total balance - SUM(NULL).
        # It could be usefull because most of the time, we are seing the
        # latest bank transactions, not the first.
        total_balance_subquery = """
            SELECT SUM(bt_sub.amount)
            FROM {table} AS bt_sub
            WHERE
                bt_sub.account_id = %s
                AND (
                    bt_sub.date < {table}.date
                    OR (
                        bt_sub.date = {table}.date
                        AND
                        bt_sub.id <= {table}.id
                    )
                )
            """.format(
            table=Transaction._meta.db_table,
        )

        reconciled_balance_subquery = """
            SELECT SUM(bt_sub_r.amount)
            FROM {table} AS bt_sub_r
            WHERE
                bt_sub_r.account_id = %s
                AND
                bt_sub_r.reconciled is True
                AND (
                    bt_sub_r.date < {table}.date
                    OR (
                        bt_sub_r.date = {table}.date
                        AND
                        bt_sub_r.id <= {table}.id
                    )
                )""".format(
            table=Transaction._meta.db_table,
        )

        return qs.extra(
            select=OrderedDict([
                ('balance_total', total_balance_subquery),
                ('balance_reconciled', reconciled_balance_subquery),
            ]),
            select_params=(account.pk, account.pk)
        )
