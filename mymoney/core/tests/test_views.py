from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings


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
