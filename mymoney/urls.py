from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from rest_framework.routers import DefaultRouter
from rest_framework_swagger.views import get_swagger_view

from mymoney.banktransactionanalytics.views import RatioAnalyticsViewSet
from mymoney.banktransactions.views import BankTransactionViewSet
from mymoney.banktransactionschedulers import BankTransactionSchedulerViewSet
from mymoney.banktransactiontags import BankTransactionTagViewSet
from mymoney.api.users.views import LoginAPIView, LogoutAPIView
from mymoney.core.views import ConfigAPIView

router = DefaultRouter()
router.register(r'transactions', BankTransactionViewSet, base_name='transaction')
router.register(r'tags', BankTransactionTagViewSet, base_name='tag')
router.register(r'schedulers', BankTransactionSchedulerViewSet, base_name='scheduler')
router.register(r'analytics', RatioAnalyticsViewSet, base_name='analytic')

api_urls = router.urls
api_urls += [
    path('config/', ConfigAPIView.as_view(), name='config'),
    # path('auth-token', obtain_auth_token, name='obtain_token'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urls)),
]

# Serve static files in debug mode, check is done later no worry.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:  # pragma: no cover
    import debug_toolbar
    schema_view = get_swagger_view(title='MyMoney API')

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),  # For admin views

        path('explore-auth/', include('rest_framework.urls', namespace='rest_framework')),
        path('explore/', schema_view),
    ]


admin.site.site_title = 'MyMoney'
admin.site.site_header = 'MyMoney'
