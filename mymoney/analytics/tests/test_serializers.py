import datetime
from unittest import mock

from django.test import TestCase

from mymoney.core.factories import UserFactory
from mymoney.tags.factories import TagFactory

from ..serializers import RatioInputSerializer, RatioSummaryInputSerializer


class RatioInputSerializerTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_type_default(self):
        serializer = RatioInputSerializer(
            data={
                'date_start': datetime.date(2015, 11, 2),
                'date_end': datetime.date(2015, 11, 3),
            },
            context={"request": mock.Mock(user=self.user)},
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data['type'], RatioInputSerializer.SUM_DEBIT)

    def test_date_start_required(self):
        serializer = RatioInputSerializer(
            data={
                'date_start': datetime.date(2015, 11, 2),
            },
            context={"request": mock.Mock(user=self.user)},
        )
        self.assertFalse(serializer.is_valid())

    def test_date_end_required(self):
        serializer = RatioInputSerializer(
            data={
                'date_end': datetime.date(2015, 11, 3),
            },
            context={"request": mock.Mock(user=self.user)},
        )
        self.assertFalse(serializer.is_valid())

    def test_date_ranges(self):
        serializer = RatioInputSerializer(
            data={
                'date_start': datetime.date(2015, 11, 2),
                'date_end': datetime.date(2015, 11, 1),
            },
            context={"request": mock.Mock(user=self.user)},
        )
        self.assertFalse(serializer.is_valid())

    def test_sum_ranges(self):
        serializer = RatioInputSerializer(
            data={
                'date_start': datetime.date(2015, 11, 1),
                'date_end': datetime.date(2015, 11, 2),
                'sum_min': 20,
                'sum_max': 10,
            },
            context={"request": mock.Mock(user=self.user)},
        )
        self.assertFalse(serializer.is_valid())

    def test_tags_default(self):
        serializer = RatioInputSerializer(
            data={
                'date_start': datetime.date(2015, 11, 1),
                'date_end': datetime.date(2015, 11, 2),
            },
            context={"request": mock.Mock(user=self.user)},
        )
        self.assertTrue(serializer.is_valid())
        self.assertListEqual(serializer.data['tags'], [])

    def test_tags(self):
        serializer = RatioInputSerializer(
            data={
                'date_start': datetime.date(2015, 11, 1),
                'date_end': datetime.date(2015, 11, 2),
                'tags': [
                    TagFactory().pk,
                    TagFactory().pk,
                ],
            },
            context={"request": mock.Mock(user=self.user)},
        )
        self.assertTrue(serializer.is_valid())


class RatioSummaryInputSerializerTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_type_default(self):
        serializer = RatioSummaryInputSerializer(
            data={
                'date_start': datetime.date(2015, 11, 2),
                'date_end': datetime.date(2015, 11, 3),
                'tag': None,
            },
            context={"request": mock.Mock(user=self.user)},
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data['type'], RatioInputSerializer.SUM_DEBIT)

    def test_date_start_required(self):
        serializer = RatioSummaryInputSerializer(
            data={
                'date_start': datetime.date(2015, 11, 2),
                'tag': None,
            },
            context={"request": mock.Mock(user=self.user)},
        )
        self.assertFalse(serializer.is_valid())

    def test_date_end_required(self):
        serializer = RatioSummaryInputSerializer(
            data={
                'date_end': datetime.date(2015, 11, 3),
                'tag': None,
            },
            context={"request": mock.Mock(user=self.user)},
        )
        self.assertFalse(serializer.is_valid())

    def test_date_ranges(self):
        serializer = RatioSummaryInputSerializer(
            data={
                'date_start': datetime.date(2015, 11, 2),
                'date_end': datetime.date(2015, 11, 1),
            },
            context={"request": mock.Mock(user=self.user)},
        )
        self.assertFalse(serializer.is_valid())

    def test_tag_required(self):
        serializer = RatioSummaryInputSerializer(
            data={
                'date_start': datetime.date(2015, 11, 1),
                'date_end': datetime.date(2015, 11, 2),
            },
            context={"request": mock.Mock(user=self.user)},
        )
        self.assertFalse(serializer.is_valid())

    def test_tag_none(self):
        serializer = RatioSummaryInputSerializer(
            data={
                'date_start': datetime.date(2015, 11, 1),
                'date_end': datetime.date(2015, 11, 2),
                'tag': None,
            },
            context={"request": mock.Mock(user=self.user)},
        )
        self.assertTrue(serializer.is_valid())
        self.assertIsNone(serializer.data['tag'])

    def test_tag(self):
        tag = TagFactory()
        serializer = RatioSummaryInputSerializer(
            data={
                'date_start': datetime.date(2015, 11, 1),
                'date_end': datetime.date(2015, 11, 2),
                'tag': tag.pk,
            },
            context={"request": mock.Mock(user=self.user)},
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data['tag'], tag.pk)
