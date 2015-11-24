from rest_framework import serializers

from mymoney.api.banktransactions.serializers import \
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
        # WARNING - read only fields are copied into shared parent extra_kwargs!
        # As a consequence, 'reconciled' field would be in read-only mode for
        # BankTransactionSerializer. Instead, by using an explicit copy for
        # extra_kwargs, we won't alter share parent property.
        extra_kwargs = BaseBankTransactionSerializer.Meta.extra_kwargs.copy()


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
