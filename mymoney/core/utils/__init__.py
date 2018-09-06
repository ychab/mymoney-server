from .currencies import *  # NOQA
from .dates import *  # NOQA


def get_default_account():
    from mymoney.accounts.models import Account
    return Account.objects.first()
