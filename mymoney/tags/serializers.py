from rest_framework import serializers

from mymoney.api.users.serializers import UserSerializer

from .models import BankTransactionTag


class BankTransactionTagInputSerializer(serializers.ModelSerializer):

    class Meta:
        model = BankTransactionTag
        fields = ('id', 'name', 'owner')
        read_only_fields = ('owner',)
        extra_kwargs = {'owner': {'default': serializers.CurrentUserDefault()}}


class BankTransactionTagOutputSerializer(serializers.ModelSerializer):
    owner = UserSerializer()

    class Meta:
        model = BankTransactionTag
        fields = ('id', 'name', 'owner')
        read_only_fields = list(fields)


class BankTransactionTagTeaserOutputSerializer(serializers.ModelSerializer):

    class Meta:
        model = BankTransactionTag
        fields = ('id', 'name',)
        read_only_fields = list(fields)
