from rest_framework import serializers

from mymoney.banktransactions import \
    BaseBankTransactionSerializer

from .models import BankTransactionScheduler


class BankTransactionSchedulerSerializer(BaseBankTransactionSerializer):

    class Meta(BaseBankTransactionSerializer.Meta):
        model = BankTransactionScheduler
        fields = (
            BaseBankTransactionSerializer.Meta.fields + (
                'type', 'recurrence', 'last_action', 'state')
        )
        read_only_fields = (
            BaseBankTransactionSerializer.Meta.read_only_fields + (
                'reconciled', 'last_action', 'state'))


class BankTransactionSchedulerCreateSerializer(BankTransactionSchedulerSerializer):
    start_now = serializers.BooleanField(default=False, write_only=True)

    class Meta(BankTransactionSchedulerSerializer.Meta):
        fields = (
            BankTransactionSchedulerSerializer.Meta.fields + ('start_now',)
        )

    def create(self, validated_data):
        start_now = validated_data.pop('start_now', False)
        instance = super(
            BankTransactionSchedulerCreateSerializer, self).create(validated_data)

        if start_now:
            instance.clone()

        return instance
