from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from rest_framework.reverse import reverse as reverse_api
from rest_framework.test import APITestCase

from mymoney.banktransactions import BankTransaction
from mymoney.api.users.factories import UserFactory


class HomeViewTestCase(TestCase):

    def test_access(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_no_dist(self):
        mymoney_settings = settings.MYMONEY.copy()
        mymoney_settings['USE_L10N_DIST'] = False
        with self.settings(MYMONEY=mymoney_settings):
            response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('dist_l10n_src', response.context)

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_dist_fr_fr(self):
        mymoney_settings = settings.MYMONEY.copy()
        mymoney_settings['USE_L10N_DIST'] = True
        with self.settings(MYMONEY=mymoney_settings):
            response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            'mymoney/dist/js/locales/fr_FR.min.js',
            response.context['dist_l10n_src'],
        )

    @override_settings(LANGUAGE_CODE='fr')
    def test_dist_fr(self):
        """
        Not recommanded, you MUST use full locale code.
        """
        mymoney_settings = settings.MYMONEY.copy()
        mymoney_settings['USE_L10N_DIST'] = True
        with self.settings(MYMONEY=mymoney_settings):
            response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            'mymoney/dist/js/locales/fr.min.js',
            response.context['dist_l10n_src'],
        )


class ConfigAPITestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse_api('config')

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
            BankTransaction.PAYMENT_METHOD_CASH,
            response.data['payment_methods'],
        )

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_payment_methods_localize(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.data['payment_methods'][BankTransaction.PAYMENT_METHOD_CASH],
            'Espèce',
        )

    def test_statuses(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertIn(BankTransaction.STATUS_IGNORED, response.data['statuses'])

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_statuses_localize(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.data['statuses'][BankTransaction.STATUS_IGNORED], 'Ignoré')
