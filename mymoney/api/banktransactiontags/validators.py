from django.utils.translation import ugettext as _

from rest_framework import exceptions

from .models import BankTransactionTag


class BaseBankTransactionTagOwnerValidator(object):

    def __init__(self):
        self.user = None

    def set_context(self, serializer_field):
        self.user = serializer_field.context['request'].user

    def __call__(self, value):
        raise NotImplementedError

    def get_queryset(self):
        return BankTransactionTag.objects.get_user_tags_queryset(self.user)


class BankTransactionTagOwnerValidator(BaseBankTransactionTagOwnerValidator):

    def __call__(self, value):
        queryset = self.get_queryset()
        queryset = queryset.filter(pk=value.pk)
        if not queryset.exists():
            raise exceptions.ValidationError(_(
                'You are not owner of the bank transaction tag.'))


class BankTransactionTagsOwnerValidator(BaseBankTransactionTagOwnerValidator):

    def __init__(self, field, *args, **kwargs):
        super(BankTransactionTagsOwnerValidator, self).__init__(*args, **kwargs)
        self.field = field

    def __call__(self, data):
        values = data.get(self.field, [])
        ids = set([t.pk for t in values])

        if ids:
            queryset = self.get_queryset()
            queryset = queryset.filter(pk__in=ids)
            if ids != set([obj.pk for obj in queryset]):
                raise exceptions.ValidationError(_(
                    'You are not owner of all bank transaction tags.'))
