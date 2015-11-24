from django.test import TestCase

from rest_framework import serializers

from ..validators import MinMaxValidator


class MinMaxValidatorTestCase(TestCase):

    def test_no_min(self):
        validator = MinMaxValidator(field_min='min', field_max='max')
        validator(data={'max': 10})

    def test_no_max(self):
        validator = MinMaxValidator(field_min='min', field_max='max')
        validator(data={'min': 10})

    def test_zero_lower(self):
        validator = MinMaxValidator(field_min='min', field_max='max')
        validator(data={'min': 0, 'max': 10})

    def test_zero_greater(self):
        validator = MinMaxValidator(field_min='min', field_max='max')
        with self.assertRaises(serializers.ValidationError):
            validator(data={'min': 10, 'max': 0})

    def test_greater(self):
        validator = MinMaxValidator(field_min='min', field_max='max')
        with self.assertRaises(serializers.ValidationError):
            validator(data={'min': -10, 'max': -20})

    def test_equal(self):
        validator = MinMaxValidator(field_min='min', field_max='max')
        validator(data={'min': 5.5, 'max': 5.5})

    def test_lower(self):
        validator = MinMaxValidator(field_min='min', field_max='max')
        validator(data={'min': 5.4, 'max': 5.5})
