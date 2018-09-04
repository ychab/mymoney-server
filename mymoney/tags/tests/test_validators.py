from unittest import mock

from django.test import TestCase

from rest_framework import exceptions

from mymoney.api.bankaccounts.factories import BankAccountFactory
from mymoney.api.users.factories import UserFactory

from ..factories import BankTransactionTagFactory
from ..validators import (
    BankTransactionTagOwnerValidator, BankTransactionTagsOwnerValidator,
)


class BankTransactionTagOwnerValidatorTestCase(TestCase):

    def test_tag_not_owner(self):
        user = UserFactory()
        tag = BankTransactionTagFactory()

        validator = BankTransactionTagOwnerValidator()
        validator.set_context(mock.Mock(context={
            "request": mock.Mock(user=user)
        }))
        with self.assertRaises(exceptions.ValidationError):
            validator(tag)

    def test_tag_owner(self):
        user = UserFactory()
        tag = BankTransactionTagFactory(owner=user)

        validator = BankTransactionTagOwnerValidator()
        validator.set_context(mock.Mock(context={
            "request": mock.Mock(user=user)
        }))
        validator(tag)

    def test_tag_owner_by_relationship(self):
        user = UserFactory()
        owner = UserFactory()
        BankAccountFactory(owners=[user, owner])
        tag = BankTransactionTagFactory(owner=owner)

        validator = BankTransactionTagOwnerValidator()
        validator.set_context(mock.Mock(context={
            "request": mock.Mock(user=user)
        }))
        validator(tag)


class BankTransactionTagsOwnerValidatorTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.bankaccount = BankAccountFactory(owners=[cls.user])
        cls.tag = BankTransactionTagFactory(owner=cls.user)
        cls.context = mock.Mock(context={'request': mock.Mock(user=cls.user)})

    def test_not_owner(self):
        validator = BankTransactionTagsOwnerValidator('tags')
        validator.set_context(self.context)
        with self.assertRaises(exceptions.ValidationError):
            validator({'tags': [BankTransactionTagFactory()]})

    def test_owner_some(self):
        validator = BankTransactionTagsOwnerValidator('tags')
        validator.set_context(self.context)
        with self.assertRaises(exceptions.ValidationError):
            validator({
                'tags': [
                    self.tag,
                    BankTransactionTagFactory(),
                ],
            })

    def test_owner_strict(self):
        validator = BankTransactionTagsOwnerValidator('tags')
        validator.set_context(self.context)
        validator({'tags': [self.tag]})

    def test_owner_by_relationship(self):
        user = UserFactory()
        self.bankaccount.owners.add(user)
        tag = BankTransactionTagFactory(owner=user)

        validator = BankTransactionTagsOwnerValidator('tags')
        validator.set_context(self.context)
        validator({'tags': [tag]})

    def test_owner_all(self):
        user = UserFactory()
        self.bankaccount.owners.add(user)
        tag = BankTransactionTagFactory(owner=user)

        validator = BankTransactionTagsOwnerValidator('tags')
        validator.set_context(self.context)
        validator({'tags': [self.tag, tag]})
