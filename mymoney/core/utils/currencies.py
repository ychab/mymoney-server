import operator
from decimal import Decimal

from django.utils.formats import get_format, localize
from django.utils.translation import get_language, to_locale

from babel import numbers
from babel.core import Locale


def get_currencies():
    """
    Returns a list of currencies.
    """
    return sorted(
        Locale.default().currencies.items(),
        key=operator.itemgetter(1)
    )


def format_currency(amount, currency):
    """
    Format an amount with the currency given for the current active language.
    """
    format = get_format('CURRENCY_PATTERN_FORMAT')
    if format == 'CURRENCY_PATTERN_FORMAT':
        format = None
    locale = to_locale(get_language())

    return numbers.format_currency(
        amount, currency, format=format, locale=locale
    )


def localize_signed_amount(amount):
    """
    Localize a number and set a positive prefix.
    """
    prefix = '+' if amount is not None and Decimal(amount) > 0 else ''
    return prefix + localize(amount)


def localize_signed_amount_currency(amount, currency):
    """
    Format an amount with its currency and set a positive prefix.
    """
    prefix = '+' if Decimal(amount) > 0 else ''
    return prefix + format_currency(amount, currency)
