from unittest import mock

from django.test import TestCase

from mymoney.accounts.factories import AccountFactory
from mymoney.transactions.models import Transaction

from ..factories import SchedulerFactory
from ..models import Scheduler
from ..serializers import SchedulerCreateSerializer


class SchedulerCreateSerializerTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        obj = SchedulerFactory.build()
        cls.data = {
            i.name: getattr(obj, i.name) for i in Scheduler._meta.get_fields()
        }
        del cls.data['account']
        cls.context = {'view': mock.Mock(account=AccountFactory())}

    def tearDown(self):
        Transaction.objects.all().delete()

    def test_start_now_default(self):
        data = self.data.copy()
        serializer = SchedulerCreateSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(Transaction.objects.count(), 0)

    def test_dont_start_now(self):
        data = self.data.copy()
        data['start_now'] = False
        serializer = SchedulerCreateSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(Transaction.objects.count(), 0)

    def test_start_now(self):
        data = self.data.copy()
        data['start_now'] = True
        serializer = SchedulerCreateSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(Transaction.objects.count(), 1)
