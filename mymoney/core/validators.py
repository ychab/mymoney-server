from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


class MinMaxValidator(object):

    def __init__(self, field_min, field_max):
        self.field_min = field_min
        self.field_max = field_max

    def __call__(self, data):
        min_val = data.get(self.field_min)
        max_val = data.get(self.field_max)
        if min_val is not None and max_val is not None and min_val > max_val:
            raise serializers.ValidationError(
                _('Min field must be lower or equals to max field.'))
