from rest_framework.mixins import (
    CreateModelMixin, DestroyModelMixin, ListModelMixin, UpdateModelMixin,
)
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from .models import BankTransactionTag
from .serializers import (
    BankTransactionTagInputSerializer, BankTransactionTagOutputSerializer,
)


class BankTransactionTagViewSet(CreateModelMixin, UpdateModelMixin,
                                DestroyModelMixin, ListModelMixin,
                                GenericViewSet):
    model = BankTransactionTag
    permission_classes = (IsAuthenticated, DjangoModelPermissions)

    def get_queryset(self):

        # For listing, you could view your own tags but also tags by
        # relationship.
        if self.action == 'list':
            return (
                BankTransactionTag.objects
                .get_user_tags_queryset(self.request.user)
                .select_related('owner')
                .order_by('name')
            )

        # Only strict owner could edit or delete its own tags.
        return BankTransactionTag.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return BankTransactionTagOutputSerializer
        return BankTransactionTagInputSerializer
