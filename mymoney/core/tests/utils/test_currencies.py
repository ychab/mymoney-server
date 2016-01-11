from decimal import Decimal

from django.test import TestCase, override_settings

from mymoney.core.utils.currencies import (
    format_currency, localize_signed_amount, localize_signed_amount_currency,
)


class CurrencyFormatTestCase(TestCase):

    @override_settings(LANGUAGE_CODE='en-us')
    def test_format_currency_en_us(self):
        self.assertEqual(
            format_currency(Decimal('-1547.23'), 'USD'),
            "-$1,547.23",
        )

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_format_currency_fr_fr(self):
        self.assertEqual(
            format_currency(Decimal('-1547.23'), 'EUR'),
            '-1\xa0547,23\xa0€',
        )

    @override_settings(LANGUAGE_CODE='fr')
    def test_format_currency_fr(self):
        self.assertEqual(
            format_currency(-1547, 'EUR'),
            "-1\xa0547,00\xa0€",
        )

    @override_settings(LANGUAGE_CODE='it')
    def test_format_currency_it(self):
        self.assertEqual(
            format_currency(-1547, 'EUR'),
            "-1.547,00\xa0€",
            )

    @override_settings(LANGUAGE_CODE='en-us')
    def test_localize_signed_amount_en_us(self):
        self.assertEqual(
            localize_signed_amount(Decimal('15.23')),
            '+15.23',
        )

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_localize_signed_amount_fr_fr(self):
        self.assertEqual(
            localize_signed_amount(Decimal('15.23')),
            '+15,23',
        )

    @override_settings(LANGUAGE_CODE='en-us')
    def test_localize_signed_amount_currency_en_us(self):
        self.assertEqual(
            localize_signed_amount_currency(Decimal('1547.23'), 'USD'),
            "+$1,547.23",
        )

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_localize_signed_amount_currency_fr_fr(self):
        self.assertEqual(
            localize_signed_amount_currency(Decimal('1547.23'), 'EUR'),
            '+1\xa0547,23\xa0€',
        )
