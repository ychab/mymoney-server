from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import BankAccount
from .serializers import (
    BankAccountCreateSerializer, BankAccountDetailSerializer,
    BankAccountSerializer,
)


class BankAccountViewSet(ModelViewSet):
    model = BankAccount
    permission_classes = (IsAuthenticated, DjangoModelPermissions)
    pagination_class = None

    def perform_create(self, serializer):
        serializer.save(owners=[self.request.user])

    def get_queryset(self):
        return (
            BankAccount.objects
            .filter(owners__in=[self.request.user.pk])
            .order_by('label')
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return BankAccountCreateSerializer
        elif self.action == 'retrieve':
            return BankAccountDetailSerializer
        else:
            return BankAccountSerializer
