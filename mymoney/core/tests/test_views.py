from django.test import override_settings

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from mymoney.transactions.models import Transaction

from ..factories import UserFactory


class ConfigAPITestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse('config')

    def test_access_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_authenticated(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_currencies(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertIn('EUR', response.data['currencies'])
        self.assertIn('USD', response.data['currencies'])

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_currencies_localize(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertIn(response.data['currencies']['EUR'], 'Euro')
        self.assertIn(response.data['currencies']['USD'], 'US Dollar')

    def test_payment_methods(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertIn(
            Transaction.PAYMENT_METHOD_CASH,
            response.data['payment_methods'],
        )

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_payment_methods_localize(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.data['payment_methods'][Transaction.PAYMENT_METHOD_CASH],
            'Espèce',
        )

    def test_statuses(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertIn(Transaction.STATUS_IGNORED, response.data['statuses'])

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_statuses_localize(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.data['statuses'][Transaction.STATUS_IGNORED], 'Ignoré')
