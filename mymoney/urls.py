from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter
from rest_framework_swagger.views import get_swagger_view

from mymoney.analytics.views import RatioAnalyticsViewSet
from mymoney.core.views import ConfigAPIView
from mymoney.schedulers.views import SchedulerViewSet
from mymoney.tags.views import TagViewSet
from mymoney.transactions.views import TransactionViewSet

router = DefaultRouter()
router.register(r'analytics', RatioAnalyticsViewSet, base_name='analytics-ratio')
router.register(r'schedulers', SchedulerViewSet, base_name='scheduler')
router.register(r'tags', TagViewSet, base_name='tag')
router.register(r'transactions', TransactionViewSet, base_name='transaction')

api_urls = router.urls
api_urls += [
    path('config/', ConfigAPIView.as_view(), name='config'),
    path('auth-token', obtain_auth_token, name='obtain_token'),
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
