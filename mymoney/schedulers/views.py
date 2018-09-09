from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from mymoney.core.utils import get_default_account
from mymoney.core.utils.dates import GRANULARITY_MONTH, GRANULARITY_WEEK
from mymoney.transactions.models import Transaction

from .models import Scheduler
from .serializers import SchedulerCreateSerializer, SchedulerSerializer


class SchedulerViewSet(ModelViewSet):
    filter_backends = (OrderingFilter,)
    ordering = ('-last_action', 'type', '-id')

    def get_queryset(self):
        return Scheduler.objects.filter(account=get_default_account())

    def get_serializer_class(self):
        if self.action == 'create':
            return SchedulerCreateSerializer
        return SchedulerSerializer

    @action(methods=['get'], detail=False)
    def summary(self, request, *args, **kwargs):
        account = get_default_account()

        total_types = {
            'debit': Scheduler.objects.get_total_debit(account),
            'credit': Scheduler.objects.get_total_credit(account),
        }

        summary = {}
        total = 0
        for s_type in Scheduler.TYPES:
            key = s_type[0]
            if key in total_types['debit'] or key in total_types['credit']:

                if key == Scheduler.TYPE_WEEKLY:
                    granularity = GRANULARITY_WEEK
                else:
                    granularity = GRANULARITY_MONTH

                total_credit = total_types['credit'].get(key, 0)
                total_debit = total_types['debit'].get(key, 0)
                used = Transaction.objects.get_total_unscheduled_period(
                    account, granularity) or 0

                summary[key] = {
                    'title': s_type[1],
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
