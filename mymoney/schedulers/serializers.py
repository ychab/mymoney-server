from rest_framework import serializers

from mymoney.transactions.serializers import BaseTransactionSerializer

from .models import Scheduler


class SchedulerSerializer(BaseTransactionSerializer):

    class Meta(BaseTransactionSerializer.Meta):
        model = Scheduler
        fields = BaseTransactionSerializer.Meta.fields + (
            'type', 'recurrence', 'last_action', 'state',
        )
        read_only_fields = ('reconciled', 'last_action', 'state')


class SchedulerCreateSerializer(SchedulerSerializer):
    start_now = serializers.BooleanField(default=False, write_only=True)

    class Meta(SchedulerSerializer.Meta):
        fields = SchedulerSerializer.Meta.fields + ('start_now',)

    def create(self, validated_data):
        start_now = validated_data.pop('start_now', False)
        instance = super().create(validated_data)

        if start_now:
            instance.clone()

        return instance
