from rest_framework.routers import DefaultRouter, DynamicListRoute, Route


class BankAccountRouter(DefaultRouter):
    """
    Custom router to alter default listing routes by prepending a bank account
    context for convenience. To prevent conflicts, also preprend it with a
    custom hardcoded prefix.
    """
    routes = list(DefaultRouter.routes)
    routes[0] = Route(
        url=r'^{prefix}/bank-account/(?P<bankaccount_pk>\d+){trailing_slash}$',
        mapping={
            'get': 'list',
            'post': 'create',
            'patch': 'partial_update_multiple',
            'delete': 'delete_multiple',
        },
        name='{basename}-list',
        initkwargs={'suffix': 'List'}
    )
    routes[1] = DynamicListRoute(
        url=r'^{prefix}/bank-account/(?P<bankaccount_pk>\d+)/{methodname}{trailing_slash}$',
        name='{basename}-{methodnamehyphen}',
        initkwargs={}
    )
