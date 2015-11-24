from unittest import mock

from django.test import override_settings

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from mymoney.api.users.factories import UserFactory

from ..factories import BankAccountFactory


@override_settings(ROOT_URLCONF='mymoney.api.bankaccounts.tests.urls')
class BankAccountContextTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.bankaccount = BankAccountFactory(owners=[cls.user])

    def test_list_bankaccount_preload(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('contexttest-list', kwargs={
            'bankaccount_pk': self.bankaccount.pk,
        }))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, str(self.bankaccount.pk))

    def test_list_bankaccount_unknown(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('contexttest-list', kwargs={
            'bankaccount_pk': 99999999999999999,
        }))
        self.assertEqual(response.status_code, 404)

    def test_list_not_owner(self):
        bankaccount = BankAccountFactory()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('contexttest-list', kwargs={
            'bankaccount_pk': bankaccount.pk,
        }))
        self.assertEqual(response.status_code, 403)

    def test_list_filter_queryset(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('contexttest-test-list-filter-queryset', kwargs={
            'bankaccount_pk': self.bankaccount.pk,
        }))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, str(self.bankaccount.pk))

    @mock.patch('rest_framework.generics.GenericAPIView.get_object')
    def test_detail_bankaccount_preload(self, mock_obj):
        mock_obj.return_value = mock.Mock(bankaccount=self.bankaccount)
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('contexttest-detail', kwargs={
            'pk': 1,
        }))
        self.assertEqual(response.status_code, 200)

    @mock.patch('rest_framework.generics.GenericAPIView.get_object')
    def test_detail_not_owner(self, mock_obj):
        bankaccount = BankAccountFactory()
        mock_obj.return_value = mock.Mock(bankaccount=bankaccount)
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('contexttest-detail', kwargs={
            'pk': 1,
        }))
        self.assertEqual(response.status_code, 403)

    @mock.patch('rest_framework.generics.GenericAPIView.get_object')
    def test_detail_filter_queryset(self, mock_obj):
        mock_obj.return_value = mock.Mock(bankaccount=self.bankaccount)
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('contexttest-test-detail-filter-queryset', kwargs={
            'pk': 1,
        }))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data)
