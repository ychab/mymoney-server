from django.test import override_settings

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase


@override_settings(ROOT_URLCONF='mymoney.api.bankaccounts.tests.urls')
class BankAccountRouterTestCase(APITestCase):

    def test_dynamic_list_route(self):
        response = self.client.get(reverse('routertest-test-list-route', kwargs={
            'bankaccount_pk': 1,
        }))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, '1')

    def test_partial_update_multiple(self):
        response = self.client.patch(reverse('routertest-list', kwargs={
            'bankaccount_pk': 1,
        }))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, '1')

    def test_delete_multiple(self):
        response = self.client.delete(reverse('routertest-list', kwargs={
            'bankaccount_pk': 1,
        }))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, '1')
