from .currencies import *
from .dates import *


def get_default_account():
    from mymoney.accounts.models import Account
    return Account.objects.first()
