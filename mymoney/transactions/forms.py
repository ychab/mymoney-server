from django import forms

from rest_framework import serializers

from mymoney.core.validators import MinMaxValidator


class TransactionFilterForm(forms.Form):

    def clean(self):
        cleaned_data = super().clean()

        field_ranges = ('amount', 'date')
        for field in field_ranges:
            if cleaned_data.get(field):
                validator = MinMaxValidator('start', 'stop')

                try:
                    validator({
                        'start': cleaned_data[field].start,
                        'stop': cleaned_data[field].stop,
                    })
                except serializers.ValidationError as exc:
                    raise forms.ValidationError(exc.detail)

        return cleaned_data
