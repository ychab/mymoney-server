from rest_framework.permissions import BasePermission


class IsBankAccountOwner(BasePermission):

    def has_permission(self, request, view):
        return view.bankaccount.owners.filter(pk=request.user.pk).exists()
