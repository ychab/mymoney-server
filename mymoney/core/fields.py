import datetime

from rest_framework import serializers


class TimestampMillisecond(serializers.Field):

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            return datetime.date.fromtimestamp(int(data) / 1000)
        except Exception:
            raise serializers.ValidationError('Invalid date.')
