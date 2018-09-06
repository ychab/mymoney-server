from collections import OrderedDict

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError

from rest_framework import exceptions, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet

from mymoney.bankaccounts import BankAccountContext
from mymoney.bankaccounts import IsBankAccountOwner

from .filters import BankTransactionFilter, BankTransactionFilterBackend
from .models import Transaction
from .serializers import (
    BankTransactionDeleteMutipleSerializer,
    BankTransactionDetailExtraSerializer, BankTransactionDetailSerializer,
    BankTransactionPartialUpdateMutipleSerializer, BankTransactionSerializer,
)


class BankTransactionViewSet(BankAccountContext, ModelViewSet):
    model = Transaction
    queryset = Transaction.objects.all()
    permission_classes = (IsBankAccountOwner, DjangoModelPermissions)
    filter_backends = (SearchFilter, BankTransactionFilterBackend, OrderingFilter,)
    search_fields = ('label',)
    filter_class = BankTransactionFilter
    ordering_fields = ('label', 'date')
    ordering = ('-date',)

    def filter_queryset(self, queryset):
        # Convert filter form errors raised.
        try:
            return super(BankTransactionViewSet, self).filter_queryset(queryset)
        except ValidationError as exc:
            raise exceptions.ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY if k == NON_FIELD_ERRORS else k: v
                 for k, v in exc.message_dict.items()})

    def get_serializer_class(self):
        if self.action == 'list':
            return BankTransactionDetailExtraSerializer
        elif self.action == 'retrieve':
            return BankTransactionDetailSerializer
        return BankTransactionSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.order_by(*(queryset.query.order_by + ['-id']))
        queryset = self.add_queryset_extra_fields(queryset)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def partial_update_multiple(self, request, *args, **kwargs):
        serializer = BankTransactionPartialUpdateMutipleSerializer(
            data=request.data, context={'request': request})

        serializer.is_valid(raise_exception=True)
        fields = {k: v for k, v in serializer.data.items() if k not in ('ids',)}

        banktransactions = Transaction.objects.filter(pk__in=serializer.data['ids'])
        for banktransaction in banktransactions:
            for field, value in fields.items():
                setattr(banktransaction, field, value)
            banktransaction.save(update_fields=fields.keys())

        return Response()

    def delete_multiple(self, request, *args, **kwargs):
        serializer = BankTransactionDeleteMutipleSerializer(
            data=request.data, context={'request': request})

        serializer.is_valid(raise_exception=True)

        banktransactions = Transaction.objects.filter(pk__in=serializer.data['ids'])
        for banktransaction in banktransactions:
            banktransaction.delete()

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
