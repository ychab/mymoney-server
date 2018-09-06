from unittest import mock

from django.test import TestCase

from mymoney.bankaccounts import BankAccountFactory
from mymoney.banktransactions import BankTransaction

from ..factories import BankTransactionSchedulerFactory
from ..models import BankTransactionScheduler
from ..serializers import BankTransactionSchedulerCreateSerializer


class BankTransactionSchedulerCreateSerializerTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        obj = BankTransactionSchedulerFactory.build()
        cls.data = {
            i.name: getattr(obj, i.name) for i in BankTransactionScheduler._meta.get_fields()
        }
        del cls.data['bankaccount']
        cls.context = {'view': mock.Mock(bankaccount=BankAccountFactory())}

    def tearDown(self):
        BankTransaction.objects.all().delete()

    def test_start_now_default(self):
        data = self.data.copy()
        serializer = BankTransactionSchedulerCreateSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(BankTransaction.objects.count(), 0)

    def test_dont_start_now(self):
        data = self.data.copy()
        data['start_now'] = False
        serializer = BankTransactionSchedulerCreateSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(BankTransaction.objects.count(), 0)

    def test_start_now(self):
        data = self.data.copy()
        data['start_now'] = True
        serializer = BankTransactionSchedulerCreateSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(BankTransaction.objects.count(), 1)
