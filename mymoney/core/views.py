from django.conf import settings
from django.utils.translation import get_language, to_locale
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = 'base.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data()
        locale = to_locale(get_language())

        if settings.MYMONEY['USE_L10N_DIST']:
            context['dist_l10n_src'] = \
                "mymoney/dist/js/locales/{locale}.min.js".format(locale=locale)

        return context
