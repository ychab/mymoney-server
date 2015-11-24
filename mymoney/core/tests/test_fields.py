import datetime
import time

from django.test import TestCase

from rest_framework import serializers

from ..fields import TimestampMillisecond


class TimestampMillisecondTestCase(TestCase):

    def test_to_internal_value_string_invalid(self):
        field = TimestampMillisecond()
        with self.assertRaises(serializers.ValidationError):
            field.to_internal_value('foo')

    def test_to_internal_value_string_integer(self):
        field = TimestampMillisecond()
        datetime_ori = datetime.datetime(2015, 10, 29, 0, 0, 0, 0)
        timestamp = int(time.mktime(datetime_ori.timetuple()))
        date_ret = field.to_internal_value(str(timestamp * 1000))
        self.assertEqual(datetime_ori.date(), date_ret)

    def test_to_internal_value_string_float(self):
        field = TimestampMillisecond()
        datetime_ori = datetime.datetime(2015, 10, 29, 0, 0, 0, 0)
        timestamp = time.mktime(datetime_ori.timetuple())
        with self.assertRaises(serializers.ValidationError):
            field.to_internal_value(str(timestamp * 1000))

    def test_to_internal_value_timestamp_second(self):
        field = TimestampMillisecond()
        datetime_ori = datetime.datetime(2015, 10, 29, 0, 0, 0, 0)
        timestamp = time.mktime(datetime_ori.timetuple())
        date_ret = field.to_internal_value(timestamp)
        self.assertEqual(date_ret.year, 1970)

    def test_to_internal_value(self):
        field = TimestampMillisecond()
        datetime_ori = datetime.datetime(2015, 10, 29, 0, 0, 0, 0)
        timestamp = time.mktime(datetime_ori.timetuple())
        date_ret = field.to_internal_value(timestamp * 1000)
        self.assertEqual(date_ret, datetime_ori.date())
