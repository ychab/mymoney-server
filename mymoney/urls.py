from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

from mymoney.core.views import HomeView

urlpatterns = [
    url(r'^', include('mymoney.api.urls')),
    url(r'^{base_url}/'.format(base_url=settings.MYMONEY['ADMIN_BASE_URL']),
        include(admin.site.urls)),
    url(r'^$', HomeView.as_view(), name='home'),
]

admin.site.site_header = 'MyMoney'
