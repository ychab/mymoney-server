
from django.conf.urls import include, url

from rest_framework.routers import DefaultRouter

from mymoney.api.bankaccounts.routers import BankAccountRouter
from mymoney.api.bankaccounts.views import BankAccountViewSet
from mymoney.api.banktransactions.views import BankTransactionViewSet
from mymoney.api.banktransactionschedulers.views import \
    BankTransactionSchedulerViewSet
from mymoney.api.banktransactiontags.views import BankTransactionTagViewSet
from mymoney.api.users.views import LoginAPIView, LogoutAPIView, UserViewSet
from mymoney.core.views import ConfigAPIView

user_router = DefaultRouter()
user_router.register(
    r'', UserViewSet, base_name='user')

bankaccounts_router = DefaultRouter()
bankaccounts_router.register(
    r'', BankAccountViewSet, base_name='bankaccount')

banktransactions_router = BankAccountRouter()
banktransactions_router.register(
    r'', BankTransactionViewSet, base_name='banktransaction')

banktransactiontags_router = DefaultRouter()
banktransactiontags_router.register(
    r'', BankTransactionTagViewSet, base_name='banktransactiontag')

banktransactionschedulers_router = BankAccountRouter()
banktransactionschedulers_router.register(
    r'', BankTransactionSchedulerViewSet, base_name='banktransactionscheduler')

urlpatterns = [
    url(r'^config/$', ConfigAPIView.as_view(), name='config'),
    url(r'^login/$', LoginAPIView.as_view(), name='login'),
    url(r'^logout/$', LogoutAPIView.as_view(), name='logout'),
    url(
        r'^user', include(
            user_router.urls, namespace='user'),
    ),
    url(
        r'^bank-accounts', include(
            bankaccounts_router.urls, namespace='bankaccounts'),
    ),
    url(
        r'^bank-transactions', include(
            banktransactions_router.urls, namespace='banktransactions')
    ),
    url(
        r'^bank-transaction-tags', include(
            banktransactiontags_router.urls, namespace='banktransactiontags'),
    ),
    url(
        r'^bank-transaction-schedulers', include(
            banktransactionschedulers_router.urls, namespace='banktransactionschedulers'),
    ),
    url(
        r'^bank-transaction-analytics/', include(
            'mymoney.api.banktransactionanalytics.urls',
            namespace='banktransactionanalytics',
        ),
    ),
]
