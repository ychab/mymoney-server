from rest_framework.response import Response
from rest_framework.views import APIView

from mymoney.banktransactions import BankTransaction

from .utils.currencies import get_currencies


class ConfigAPIView(APIView):

    def get(self, request, *args, **kwargs):
        return Response({
            'currencies': dict(get_currencies()),
            'payment_methods': dict(BankTransaction.PAYMENT_METHODS),
            'statuses': dict(BankTransaction.STATUSES),
        })
