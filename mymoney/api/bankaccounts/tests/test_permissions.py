from unittest import mock

from django.test import TestCase

from mymoney.api.users.factories import UserFactory

from ..factories import BankAccountFactory
from ..permissions import IsBankAccountOwner


class IsBankAccountOwnerTestCase(TestCase):

    def test_not_owner(self):
        self.assertFalse(IsBankAccountOwner().has_permission(
            mock.Mock(user=UserFactory()),
            mock.Mock(bankaccount=BankAccountFactory()),
        ))

    def test_owner_allowed(self):
        user = UserFactory()
        bankaccount = BankAccountFactory(owners=[user])
        self.assertTrue(IsBankAccountOwner().has_permission(
            mock.Mock(user=user),
            mock.Mock(bankaccount=bankaccount),
        ))
