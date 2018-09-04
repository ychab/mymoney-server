from rest_framework.decorators import list_route
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import (
    CreateModelMixin, DestroyModelMixin, ListModelMixin, UpdateModelMixin,
)
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from mymoney.api.bankaccounts.mixins import BankAccountContext
from mymoney.api.bankaccounts.permissions import IsBankAccountOwner
from mymoney.banktransactions import BankTransaction
from mymoney.core.utils.dates import GRANULARITY_MONTH, GRANULARITY_WEEK

from .models import BankTransactionScheduler
from .serializers import (
    BankTransactionSchedulerCreateSerializer,
    BankTransactionSchedulerSerializer,
)


class BankTransactionSchedulerViewSet(BankAccountContext, CreateModelMixin,
                                      UpdateModelMixin, DestroyModelMixin,
                                      ListModelMixin, GenericViewSet):

    model = BankTransactionScheduler
    queryset = BankTransactionScheduler.objects.all()
    permission_classes = (IsBankAccountOwner, DjangoModelPermissions)
    filter_backends = (OrderingFilter,)
    ordering = ('-last_action', 'type', '-id')

    def get_serializer_class(self):
        if self.action == 'create':
            return BankTransactionSchedulerCreateSerializer
        return BankTransactionSchedulerSerializer

    @list_route(['get'])
    def summary(self, request, *args, **kwargs):
        total_types = {
            'debit': BankTransactionScheduler.objects.get_total_debit(self.bankaccount),
            'credit': BankTransactionScheduler.objects.get_total_credit(self.bankaccount),
        }

        summary = {}
        total = 0
        for bts_type in BankTransactionScheduler.TYPES:
            key = bts_type[0]
            if key in total_types['debit'] or key in total_types['credit']:

                if key == BankTransactionScheduler.TYPE_WEEKLY:
                    granularity = GRANULARITY_WEEK
                else:
                    granularity = GRANULARITY_MONTH

                total_credit = total_types['credit'].get(key, 0)
                total_debit = total_types['debit'].get(key, 0)
                used = BankTransaction.objects.get_total_unscheduled_period(
                    self.bankaccount, granularity) or 0

                summary[key] = {
                    'title': bts_type[1],
                    'credit': total_credit,
                    'debit': total_debit,
                    'used': used,
                    'remaining': total_credit + total_debit + used,
                    'total': total_credit + total_debit
                }
                total += summary[key]['total']

        return Response({
            'summary': summary,
            'total': total,
        })
