from unittest import mock

from rest_framework.decorators import detail_route, list_route
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from ..mixins import BankAccountContext
from ..routers import BankAccountRouter

urlpatterns = []


class RouterTestViewSet(GenericViewSet):

    permission_classes = (AllowAny,)

    @list_route(['get'])
    def test_list_route(self, request, bankaccount_pk, *args, **kwargs):
        return Response(bankaccount_pk)

    def partial_update_multiple(self, request, bankaccount_pk, *args, **kwargs):
        return Response(bankaccount_pk)

    def delete_multiple(self, request, bankaccount_pk, *args, **kwargs):
        return Response(bankaccount_pk)


router = BankAccountRouter()
router.register(r'routertest', RouterTestViewSet, base_name='routertest')
urlpatterns += router.urls


class ContextTestViewSet(BankAccountContext, GenericViewSet):

    def list(self, request, bankaccount_pk, *args, **kwargs):
        return Response(bankaccount_pk)

    def retrieve(self, request, *args, **kwargs):
        return Response()

    @list_route(['get'])
    def test_list_filter_queryset(self, request, *args, **kwargs):
        qs = mock.Mock()
        qs.bankaccount_pk = None

        def mock_filters(**kwargs):
            qs.bankaccount_pk = kwargs.get('bankaccount__pk', None)

        qs = mock.Mock()
        qs.filter.side_effect = mock_filters
        self.filter_queryset(qs)
        return Response(qs.bankaccount_pk)

    @detail_route(['get'])
    def test_detail_filter_queryset(self, request, *args, **kwargs):
        qs = mock.Mock()
        qs.bankaccount_pk = None

        def mock_filters(**kwargs):  # pragma: no cover
            qs.bankaccount_pk = kwargs.get('bankaccount__pk', None)

        qs.filter.side_effect = mock_filters
        self.filter_queryset(qs)
        return Response(qs.bankaccount_pk)

router = BankAccountRouter()
router.register(r'contexttest', ContextTestViewSet, base_name='contexttest')
urlpatterns += router.urls
