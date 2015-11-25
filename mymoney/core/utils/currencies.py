import operator
from decimal import Decimal

from django.utils.formats import get_format_modules, localize
from django.utils.translation import get_language, to_locale

from babel import numbers
from babel.core import Locale

CACHE_FORMAT = {}


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
    lang = get_language()
    format = get_format('CURRENCY_PATTERN_FORMAT', lang)
    locale = to_locale(lang)

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


def get_format(format_type, lang):
    """
    Ugly workaround to security fix of 1.8.7 django.utils.formats.get_format
    which now exclude custom formats with frozenset FORMAT_SETTINGS ...
    """
    cache_key = (format_type, lang)
    if cache_key not in CACHE_FORMAT:
        format = None
        for module in get_format_modules(lang):
            try:
                format = getattr(module, format_type)
                break
            except AttributeError:
                continue
        CACHE_FORMAT[cache_key] = format

    return CACHE_FORMAT[cache_key]
