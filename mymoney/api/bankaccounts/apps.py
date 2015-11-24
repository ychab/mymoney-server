from django.apps import AppConfig


class BankAccountConfig(AppConfig):
    name = 'mymoney.api.bankaccounts'
    verbose_name = "Bank accounts"

    def ready(self):
        import mymoney.api.bankaccounts.signals.handlers  # noqa
