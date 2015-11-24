from datetime import date

from django.test import RequestFactory, TestCase

from ..paginators import (
    DatePaginator, EmptyPage, InvalidDateRanges, UnknownGranularity,
)
from ..utils.dates import GRANULARITY_MONTH, GRANULARITY_WEEK


class DatePaginatorTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.request = RequestFactory().request()

    def test_invalid_date_ranges_equal(self):
        with self.assertRaises(InvalidDateRanges):
            DatePaginator(date(2015, 7, 16), date(2015, 7, 16), GRANULARITY_WEEK)

    def test_invalid_date_ranges_greater(self):
        with self.assertRaises(InvalidDateRanges):
            DatePaginator(date(2015, 7, 17), date(2015, 7, 16), GRANULARITY_WEEK)

    def test_unknown_granularity(self):
        with self.assertRaises(UnknownGranularity):
            DatePaginator(date(2015, 7, 15), date(2015, 7, 16), 'foo')

    def test_empty_page_previous(self):
        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 7, 31),
            GRANULARITY_MONTH,
        )
        with self.assertRaises(EmptyPage):
            paginator.page(date(2015, 6, 30))

    def test_empty_page_next(self):
        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 7, 31),
            GRANULARITY_MONTH,
        )
        with self.assertRaises(EmptyPage):
            paginator.page(date(2015, 8, 1))

    def test_page_equal(self):
        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 7, 31),
            GRANULARITY_MONTH,
        )
        paginator.page(date(2015, 7, 1))

    def test_page_between(self):
        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 7, 31),
            GRANULARITY_MONTH,
        )
        paginator.page(date(2015, 7, 15))

    def test_previous_link_none(self):
        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 11, 15),
            GRANULARITY_MONTH,
        )
        links = paginator.get_links(date(2015, 7, 15), self.request)
        self.assertIsNone(links['previous'])

    def test_previous_link(self):
        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 11, 15),
            GRANULARITY_MONTH,
        )
        links = paginator.get_links(date(2015, 10, 15), self.request)
        self.assertEqual(
            links['previous'],
            'http://testserver/?date=2015-09-01',
        )

    def test_next_link_none(self):
        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 11, 15),
            GRANULARITY_MONTH,
        )
        links = paginator.get_links(date(2015, 11, 14), self.request)
        self.assertIsNone(links['next'])

    def test_next_link(self):
        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 11, 15),
            GRANULARITY_MONTH,
        )
        links = paginator.get_links(date(2015, 10, 15), self.request)
        self.assertEqual(
            links['next'],
            'http://testserver/?date=2015-11-01',
        )

    def test_links_none(self):
        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 7, 31),
            GRANULARITY_MONTH,
        )
        links = paginator.get_links(date(2015, 7, 15), self.request)
        self.assertIsNone(links['previous'])
        self.assertIsNone(links['next'])

    def test_links_both(self):
        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 11, 15),
            GRANULARITY_MONTH,
        )
        links = paginator.get_links(date(2015, 10, 15), self.request)
        self.assertEqual(
            links['previous'],
            'http://testserver/?date=2015-09-01',
        )
        self.assertEqual(
            links['next'],
            'http://testserver/?date=2015-11-01',
        )

    def test_link_parameter(self):
        request = RequestFactory().request(QUERY_STRING='foo=bar')
        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 11, 15),
            GRANULARITY_MONTH,
        )
        links = paginator.get_links(date(2015, 10, 15), request)
        self.assertEqual(
            links['next'],
            'http://testserver/?date=2015-11-01&foo=bar',
        )


class MonthlyDatePageTestCase(TestCase):

    def test_has_next(self):

        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 8, 31),
            GRANULARITY_MONTH,
        )
        self.assertTrue(paginator.page(date(2015, 7, 15)).has_next())
        self.assertTrue(paginator.page(date(2015, 7, 31)).has_next())
        self.assertFalse(paginator.page(date(2015, 8, 15)).has_next())

    def test_has_previous(self):

        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 8, 31),
            GRANULARITY_MONTH,
        )
        self.assertTrue(paginator.page(date(2015, 8, 15)).has_previous())
        self.assertTrue(paginator.page(date(2015, 8, 1)).has_previous())
        self.assertFalse(paginator.page(date(2015, 7, 15)).has_previous())

    def test_has_other_pages(self):

        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 8, 31),
            GRANULARITY_MONTH,
        )
        self.assertTrue(paginator.page(date(2015, 7, 15)).has_other_pages())
        self.assertTrue(paginator.page(date(2015, 7, 31)).has_other_pages())
        self.assertTrue(paginator.page(date(2015, 8, 15)).has_other_pages())
        self.assertTrue(paginator.page(date(2015, 8, 1)).has_other_pages())

        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 7, 31),
            GRANULARITY_MONTH,
        )
        self.assertFalse(paginator.page(date(2015, 7, 15)).has_other_pages())

    def test_next(self):

        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 8, 31),
            GRANULARITY_MONTH,
        )
        self.assertEqual(
            paginator.page(date(2015, 7, 15)).next_date(),
            date(2015, 8, 1)
        )
        self.assertEqual(
            paginator.page(date(2015, 7, 1)).next_date(),
            date(2015, 8, 1)
        )

    def test_previous(self):

        paginator = DatePaginator(
            date(2015, 7, 1),
            date(2015, 8, 31),
            GRANULARITY_MONTH,
        )
        self.assertEqual(
            paginator.page(date(2015, 8, 15)).previous_date(),
            date(2015, 7, 1)
        )
        self.assertEqual(
            paginator.page(date(2015, 8, 1)).previous_date(),
            date(2015, 7, 1)
        )


class WeeklyDatePageTestCase(TestCase):

    def test_has_next(self):

        with self.settings(LANGUAGE_CODE='fr-fr'):
            paginator = DatePaginator(
                date(2015, 7, 27),
                date(2015, 8, 9),
                GRANULARITY_WEEK,
            )
            self.assertTrue(paginator.page(date(2015, 7, 29)).has_next())
            self.assertTrue(paginator.page(date(2015, 8, 2)).has_next())
            self.assertFalse(paginator.page(date(2015, 8, 3)).has_next())

        with self.settings(LANGUAGE_CODE='en-us'):
            paginator = DatePaginator(
                date(2015, 7, 26),
                date(2015, 8, 8),
                GRANULARITY_WEEK,
            )
            self.assertTrue(paginator.page(date(2015, 7, 28)).has_next())
            self.assertTrue(paginator.page(date(2015, 8, 1)).has_next())
            self.assertFalse(paginator.page(date(2015, 8, 2)).has_next())

    def test_has_previous(self):

        with self.settings(LANGUAGE_CODE='fr-fr'):
            paginator = DatePaginator(
                date(2015, 7, 27),
                date(2015, 8, 9),
                GRANULARITY_WEEK,
            )
            self.assertTrue(paginator.page(date(2015, 8, 6)).has_previous())
            self.assertTrue(paginator.page(date(2015, 8, 3)).has_previous())
            self.assertFalse(paginator.page(date(2015, 8, 2)).has_previous())

        with self.settings(LANGUAGE_CODE='en-us'):
            paginator = DatePaginator(
                date(2015, 7, 26),
                date(2015, 8, 8),
                GRANULARITY_WEEK,
            )
            self.assertTrue(paginator.page(date(2015, 8, 5)).has_previous())
            self.assertTrue(paginator.page(date(2015, 8, 2)).has_previous())
            self.assertFalse(paginator.page(date(2015, 8, 1)).has_previous())

    def test_has_other_pages(self):

        with self.settings(LANGUAGE_CODE='fr-fr'):
            paginator = DatePaginator(
                date(2015, 7, 27),
                date(2015, 8, 16),
                GRANULARITY_WEEK,
            )
            self.assertTrue(paginator.page(date(2015, 8, 6)).has_other_pages())
            self.assertTrue(paginator.page(date(2015, 7, 29)).has_other_pages())
            self.assertTrue(paginator.page(date(2015, 8, 13)).has_other_pages())

            paginator = DatePaginator(
                date(2015, 7, 27),
                date(2015, 8, 2),
                GRANULARITY_WEEK,
            )
            self.assertFalse(paginator.page(date(2015, 7, 29)).has_other_pages())

        with self.settings(LANGUAGE_CODE='en-us'):
            paginator = DatePaginator(
                date(2015, 7, 26),
                date(2015, 8, 15),
                GRANULARITY_WEEK,
            )
            self.assertTrue(paginator.page(date(2015, 8, 5)).has_other_pages())
            self.assertTrue(paginator.page(date(2015, 7, 28)).has_other_pages())
            self.assertTrue(paginator.page(date(2015, 8, 12)).has_other_pages())

            paginator = DatePaginator(
                date(2015, 7, 26),
                date(2015, 8, 1),
                GRANULARITY_WEEK,
            )
            self.assertFalse(paginator.page(date(2015, 7, 28)).has_other_pages())

    def test_next(self):

        with self.settings(LANGUAGE_CODE='fr-fr'):
            paginator = DatePaginator(
                date(2015, 7, 20),
                date(2015, 8, 9),
                GRANULARITY_WEEK,
            )
            self.assertEqual(
                paginator.page(date(2015, 7, 29)).next_date(),
                date(2015, 8, 3)
            )
            self.assertEqual(
                paginator.page(date(2015, 7, 27)).next_date(),
                date(2015, 8, 3)
            )

        with self.settings(LANGUAGE_CODE='en-us'):
            paginator = DatePaginator(
                date(2015, 7, 26),
                date(2015, 8, 8),
                GRANULARITY_WEEK,
            )
            self.assertTrue(paginator.page(date(2015, 7, 28)).has_next())
            self.assertTrue(paginator.page(date(2015, 8, 1)).has_next())
            self.assertFalse(paginator.page(date(2015, 8, 2)).has_next())

    def test_previous(self):

        with self.settings(LANGUAGE_CODE='fr-fr'):
            paginator = DatePaginator(
                date(2015, 7, 27),
                date(2015, 8, 9),
                GRANULARITY_WEEK,
            )
            self.assertEqual(
                paginator.page(date(2015, 8, 9)).previous_date(),
                date(2015, 7, 27),
            )
            self.assertEqual(
                paginator.page(date(2015, 8, 3)).previous_date(),
                date(2015, 7, 27),
            )

        with self.settings(LANGUAGE_CODE='en-us'):
            paginator = DatePaginator(
                date(2015, 7, 26),
                date(2015, 8, 8),
                GRANULARITY_WEEK,
            )
            self.assertEqual(
                paginator.page(date(2015, 8, 8)).previous_date(),
                date(2015, 7, 26),
            )
            self.assertEqual(
                paginator.page(date(2015, 8, 2)).previous_date(),
                date(2015, 7, 26),
            )
