from rest_framework.generics import get_object_or_404

from .models import BankAccount
from .permissions import IsBankAccountOwner


class BankAccountContext(object):

    permission_classes = (IsBankAccountOwner,)

    def __init__(self, *args, **kwargs):
        super(BankAccountContext, self).__init__(*args, **kwargs)
        self.bankaccount = None

    def initial(self, request, bankaccount_pk=None, *args, **kwargs):

        if bankaccount_pk is not None:
            self.bankaccount = get_object_or_404(BankAccount, pk=bankaccount_pk)
        else:
            obj = self.get_object()
            self.bankaccount = obj.bankaccount

        super(BankAccountContext, self).initial(request, *args, **kwargs)

    def filter_queryset(self, queryset):

        # Filter for list route only. Could be called by detail route.
        bankaccount_pk = self.kwargs.get('bankaccount_pk')
        if bankaccount_pk:
            queryset = queryset.filter(bankaccount__pk=bankaccount_pk)

        return super(BankAccountContext, self).filter_queryset(queryset)
