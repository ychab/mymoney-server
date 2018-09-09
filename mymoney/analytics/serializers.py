from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from mymoney.core.validators import MinMaxValidator
from mymoney.tags.models import Tag
from mymoney.tags.serializers import TagSerializer


class BaseRatioSerializer(serializers.Serializer):

    SINGLE_CREDIT = 'single_credit'
    SINGLE_DEBIT = 'single_debit'
    SUM_CREDIT = 'sum_credit'
    SUM_DEBIT = 'sum_debit'
    TYPES = (
        (_('Sum'), (
            (SUM_DEBIT, _('Expenses')),
            (SUM_CREDIT, _('Income')),
        )),
        (_('Single'), (
            (SINGLE_DEBIT, _('Expenses')),
            (SINGLE_CREDIT, _('Income')),
        )),
    )

    type = serializers.ChoiceField(choices=TYPES, default=SUM_DEBIT)
    date_start = serializers.DateField()
    date_end = serializers.DateField()
    reconciled = serializers.NullBooleanField(required=False)

    class Meta:
        validators = [MinMaxValidator('date_start', 'date_end')]


class RatioInputSerializer(BaseRatioSerializer):

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        required=False,
        many=True,
        default=[],
    )
    sum_min = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
    )
    sum_max = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
    )

    class Meta(BaseRatioSerializer.Meta):
        validators = BaseRatioSerializer.Meta.validators + [
            MinMaxValidator('sum_min', 'sum_max'),
        ]


class RatioListSerializer(serializers.ListSerializer):

    def to_representation(self, data):
        ids = [i['tag'] for i in data if i != 0]
        tags = Tag.objects.in_bulk(ids)
        for row in data:
            row['tag'] = tags[row['tag']] if row['tag'] in tags else None

        return super(RatioListSerializer, self).to_representation(data)


class RatioOutputSerializer(serializers.Serializer):
    tag = TagSerializer()
    sum = serializers.DecimalField(max_digits=5, decimal_places=2)
    count = serializers.IntegerField(min_value=0)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        list_serializer_class = RatioListSerializer


class RatioSummaryInputSerializer(BaseRatioSerializer):
    tag = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        allow_null=True,
    )
