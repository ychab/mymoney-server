import json

from django.conf import settings
from django.utils.translation import get_language, to_locale
from django.views.generic import TemplateView

from rest_framework.settings import api_settings


class HomeView(TemplateView):
    template_name = 'base.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data()
        locale = to_locale(get_language())

        context['django_settings'] = json.dumps({
            'static_url': settings.STATIC_URL,
            'locale': locale,
            'xsrf_cookiename': settings.CSRF_COOKIE_NAME,
            'non_field_errors_key': api_settings.NON_FIELD_ERRORS_KEY,
            'debug': settings.DEBUG,
        })

        if settings.MYMONEY['USE_L10N_DIST']:
            context['dist_l10n_src'] = \
                "mymoney/dist/js/locales/{locale}.min.js".format(
                    locale=locale)

        return context
