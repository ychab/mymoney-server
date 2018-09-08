from collections import OrderedDict

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError

from rest_framework import exceptions, status
from rest_framework.decorators import list_route, action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet

from .models import Transaction
from .serializers import (
    TransactionDeleteMutipleSerializer,
    BankTransactionDetailExtraSerializer, BankTransactionDetailSerializer,
    TransactionPartialUpdateMutipleSerializer, TransactionSerializer,
)


class TransactionViewSet(ModelViewSet):
    queryset = Transaction.objects.all()
    filter_backends = (SearchFilter, OrderingFilter,)
    search_fields = ('label',)
    ordering_fields = ('label', 'date')
    ordering = ('-date',)

    def get_serializer_class(self):
        if self.action == 'list':
            return TransactionListSerializer
        elif self.action == 'retrieve':
            return TransactionDetailSerializer
        return TransactionSerializer

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

    @action(methods=['post'], detail=False, url_path='delete-multiple')
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

    def add_queryset_extra_fields(self, qs):
        """
        Add extra fields to the queryset.
        By using SQL and not Python, we could alter order_by and sort without
        altering the new balances fields.

        Extra fields are:
        - total_balance
        - reconciled_balance
        """
        # Unfortunetly, we cannot get it by doing the opposite (i.e :
        # total balance - SUM(futur bt) because with postgreSQL at least,
        # the last dated bank transaction would give None :
        # total balance - SUM(NULL).
        # It could be usefull because most of the time, we are seing the
        # latest bank transactions, not the first.
        total_balance_subquery = """
            SELECT SUM(bt_sub.amount) + {balance_initial}
            FROM {table} AS bt_sub
            WHERE
                bt_sub.bankaccount_id = %s
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
            balance_initial=self.bankaccount.balance_initial,
        )

        reconciled_balance_subquery = """
            SELECT SUM(bt_sub_r.amount) + {balance_initial}
            FROM {table} AS bt_sub_r
            WHERE
                bt_sub_r.bankaccount_id = %s
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
            balance_initial=self.bankaccount.balance_initial,
        )

        return qs.extra(
            select=OrderedDict([
                ('balance_total', total_balance_subquery),
                ('balance_reconciled', reconciled_balance_subquery),
            ]),
            select_params=(self.bankaccount.pk, self.bankaccount.pk)
        )
