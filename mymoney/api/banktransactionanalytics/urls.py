from mymoney.api.bankaccounts.routers import BankAccountRouter

from .views import RatioAnalyticsViewSet, TrendTimeAnalyticsViewSet

ratio_router = BankAccountRouter()
ratio_router.register(
    r'ratio', RatioAnalyticsViewSet, base_name='ratio')

trendtime_router = BankAccountRouter()
trendtime_router.register(
    r'trendtime', TrendTimeAnalyticsViewSet, base_name='trendtime')

urlpatterns = []
urlpatterns += ratio_router.urls
urlpatterns += trendtime_router.urls
