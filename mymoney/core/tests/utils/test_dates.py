import datetime

from django.test import TestCase

from mymoney.core.utils.dates import (
    GRANULARITY_MONTH, GRANULARITY_WEEK, get_date_ranges, get_datetime_ranges,
    get_weekday,
)


class DateUtilsTestCase(TestCase):

    def test_weekday(self):

        with self.settings(LANGUAGE_CODE='en-us'):
            self.assertEqual(get_weekday(), 6)

        with self.settings(LANGUAGE_CODE='fr-fr'):
            self.assertEqual(get_weekday(), 0)

        with self.settings(LANGUAGE_CODE='fa'):
            self.assertEqual(get_weekday(), 5)


class DateRangesTestCase(TestCase):

    def test_week(self):

        with self.settings(LANGUAGE_CODE='en-us'):
            s, e = get_date_ranges(
                datetime.date(2015, 4, 29), GRANULARITY_WEEK
            )
            self.assertEqual(s, datetime.date(2015, 4, 26))
            self.assertEqual(e, datetime.date(2015, 5, 2))

        with self.settings(LANGUAGE_CODE='fr-fr'):
            s, e = get_date_ranges(
                datetime.date(2015, 4, 29), GRANULARITY_WEEK
            )
            self.assertEqual(s, datetime.date(2015, 4, 27))
            self.assertEqual(e, datetime.date(2015, 5, 3))

        with self.settings(LANGUAGE_CODE='fr-fr'):
            s, e = get_date_ranges(
                datetime.date(2015, 7, 13), GRANULARITY_WEEK
            )
            self.assertEqual(s, datetime.date(2015, 7, 13))
            self.assertEqual(e, datetime.date(2015, 7, 19))

        with self.settings(LANGUAGE_CODE='fa'):
            s, e = get_date_ranges(
                datetime.date(2015, 4, 29), GRANULARITY_WEEK
            )
            self.assertEqual(s, datetime.date(2015, 4, 25))
            self.assertEqual(e, datetime.date(2015, 5, 1))

    def test_month(self):

        s, e = get_date_ranges(
            datetime.date(2015, 2, 15), GRANULARITY_MONTH
        )
        self.assertEqual(s, datetime.date(2015, 2, 1))
        self.assertEqual(e, datetime.date(2015, 2, 28))

        s, e = get_date_ranges(
            datetime.date(2016, 2, 15), GRANULARITY_MONTH
        )
        self.assertEqual(s, datetime.date(2016, 2, 1))
        self.assertEqual(e, datetime.date(2016, 2, 29))


class DatetimeRangesTestCase(TestCase):

    def test_week(self):

        with self.settings(LANGUAGE_CODE='en-us'):
            s, e = get_datetime_ranges(
                datetime.datetime(2015, 4, 29, 15, 4),
                GRANULARITY_WEEK,
            )
            self.assertEqual(s, datetime.datetime(2015, 4, 26, 0, 0, 0, 0))
            self.assertEqual(e, datetime.datetime(2015, 5, 2, 23, 59, 59, 0))

        with self.settings(LANGUAGE_CODE='fr-fr'):
            s, e = get_datetime_ranges(
                datetime.datetime(2015, 4, 29, 17, 55),
                GRANULARITY_WEEK,
            )
            self.assertEqual(s, datetime.datetime(2015, 4, 27, 0, 0, 0, 0))
            self.assertEqual(e, datetime.datetime(2015, 5, 3, 23, 59, 59, 0))

        with self.settings(LANGUAGE_CODE='fr-fr'):
            s, e = get_datetime_ranges(
                datetime.datetime(2015, 7, 13, 17, 14), GRANULARITY_WEEK
            )
            self.assertEqual(s, datetime.datetime(2015, 7, 13, 0, 0, 0, 0))
            self.assertEqual(e, datetime.datetime(2015, 7, 19, 23, 59, 59, 0))

    def test_month(self):

        s, e = get_datetime_ranges(
            datetime.datetime(2015, 2, 15, 12, 15),
            GRANULARITY_MONTH,
        )
        self.assertEqual(s, datetime.datetime(2015, 2, 1, 0, 0, 0, 0))
        self.assertEqual(e, datetime.datetime(2015, 2, 28, 23, 59, 59, 0))

        s, e = get_datetime_ranges(
            datetime.datetime(2016, 2, 15, 12, 15),
            GRANULARITY_MONTH,
        )
        self.assertEqual(s, datetime.datetime(2016, 2, 1, 0, 0, 0, 0))
        self.assertEqual(e, datetime.datetime(2016, 2, 29, 23, 59, 59, 0))
