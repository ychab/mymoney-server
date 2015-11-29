from decimal import Decimal
from unittest import mock

from rest_framework.pagination import PageNumberPagination
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from mymoney.api.users.factories import UserFactory

from ..factories import BankAccountFactory
from ..models import BankAccount


class RetrieveViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.bankaccount = BankAccountFactory(owners=[cls.user])
        cls.url = reverse('bankaccounts:bankaccount-detail', kwargs={
            'pk': cls.bankaccount.pk,
        })

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_not_owner(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_retrieve(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('balance_view', response.data)
        self.assertIn('balance_initial_view', response.data)
        self.assertIn('balance_current_view', response.data)
        self.assertIn('balance_reconciled_view', response.data)


class ListViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse('bankaccounts:bankaccount-list')

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_granted(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_no_bankaccount(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.data, [])

    def test_not_owner(self):
        user = UserFactory()
        BankAccountFactory()
        self.client.force_authenticate(user)
        response = self.client.get(self.url)
        self.assertListEqual(response.data, [])

    def test_owner(self):
        user = UserFactory()
        bankaccount = BankAccountFactory(owners=[user])
        BankAccountFactory()
        self.client.force_authenticate(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], bankaccount.pk)

    def test_order_by_label(self):
        user = UserFactory()
        ba1 = BankAccountFactory(label='foo', owners=[user])
        ba2 = BankAccountFactory(label='bar', owners=[user])
        self.client.force_authenticate(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], ba2.pk)
        self.assertEqual(response.data[1]['id'], ba1.pk)

    @mock.patch.object(
        PageNumberPagination, 'page_size', new_callable=mock.PropertyMock)
    def test_no_pagination(self, size_mock):
        limit = 2
        size_mock.return_value = limit
        total = limit + 1

        for i in range(0, total):
            BankAccountFactory(owners=[self.user])

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), total)


class CreateViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(user_permissions='all')
        cls.url = reverse('bankaccounts:bankaccount-list')

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_without_permission(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url)
        self.assertNotIn(response.status_code, [401, 403])

    def test_label_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={'currency': 'EUR'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('label', response.data)

    def test_currency_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={'label': 'foo'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('currency', response.data)

    def test_currency_invalid(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'currency': 'foo',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('currency', response.data)

    def test_default_balance(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'currency': 'USD',
        })
        self.assertEqual(response.status_code, 201)
        bankaccount = BankAccount.objects.get(pk=response.data['id'])
        self.assertEqual(bankaccount.balance, 0)
        self.assertEqual(bankaccount.balance_initial, 0)

    def test_no_balance(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'currency': 'USD',
            'balance': 150,
        })
        self.assertEqual(response.status_code, 201)
        bankaccount = BankAccount.objects.get(pk=response.data['id'])
        self.assertEqual(bankaccount.balance, 0)

    def test_balance_initial(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'currency': 'USD',
            'balance_initial': 147.23,
        })
        self.assertEqual(response.status_code, 201)
        bankaccount = BankAccount.objects.get(pk=response.data['id'])
        self.assertEqual(bankaccount.balance, Decimal('147.23'))
        self.assertEqual(bankaccount.balance_initial, Decimal('147.23'))

    def test_default_owner(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'currency': 'USD',
        })
        self.assertEqual(response.status_code, 201)
        bankaccount = BankAccount.objects.get(pk=response.data['id'])
        self.assertListEqual(
            [self.user.pk],
            [user.pk for user in bankaccount.owners.all()],
        )

    def test_create(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'currency': 'USD',
        })
        self.assertEqual(response.status_code, 201)
        bankaccount = BankAccount.objects.get(pk=response.data['id'])
        self.assertEqual(bankaccount.label, 'foo')
        self.assertEqual(bankaccount.currency, 'USD')


class PartialUpdateViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(user_permissions='all')
        cls.bankaccount = BankAccountFactory(owners=[cls.user])
        cls.url = reverse('bankaccounts:bankaccount-detail', kwargs={
            'pk': cls.bankaccount.pk,
        })

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_authenticated(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_owner_without_permission(self):
        user = UserFactory()
        bankaccount = BankAccountFactory(owners=[user])
        self.client.force_authenticate(user)
        response = self.client.patch(
            reverse('bankaccounts:bankaccount-detail', kwargs={
                'pk': bankaccount.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_access_not_owner_with_permissions(self):
        user = UserFactory(user_permissions='all')
        self.client.force_authenticate(user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 404)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 200)

    def test_owners_unchanged(self):
        bankaccount = BankAccountFactory(owners=[self.user])
        url = reverse('bankaccounts:bankaccount-detail', kwargs={
            'pk': bankaccount.pk,
        })
        user = UserFactory()
        bankaccount.owners.add(user)

        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'owners': self.user.pk,
        })
        self.assertEqual(response.status_code, 200)
        bankaccount.refresh_from_db()
        self.assertListEqual(
            [self.user.pk, user.pk],
            sorted([owner.pk for owner in bankaccount.owners.all()]),
        )

    def test_update_balance(self):
        bankaccount = BankAccountFactory(balance=15, owners=[self.user])
        url = reverse('bankaccounts:bankaccount-detail', kwargs={
            'pk': bankaccount.pk,
        })

        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'balance': 10.5,
        })
        self.assertEqual(response.status_code, 200)
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal('10.5'))

    def test_update_balance_initial(self):
        bankaccount = BankAccountFactory(balance_initial=15, owners=[self.user])
        url = reverse('bankaccounts:bankaccount-detail', kwargs={
            'pk': bankaccount.pk,
        })

        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'balance_initial': 20,
        })
        self.assertEqual(response.status_code, 200)
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal('20'))
        self.assertEqual(bankaccount.balance_initial, Decimal('20'))

        response = self.client.patch(url, data={
            'balance_initial': 9.5,
        })
        self.assertEqual(response.status_code, 200)
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal('9.5'))
        self.assertEqual(bankaccount.balance_initial, Decimal('9.5'))

    def test_update_balance_and_balance_initial(self):
        bankaccount = BankAccountFactory(
            balance=0,
            balance_initial=10,
            owners=[self.user],
        )
        url = reverse('bankaccounts:bankaccount-detail', kwargs={
            'pk': bankaccount.pk,
        })

        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'balance': 20,
            'balance_initial': 5,
        })
        self.assertEqual(response.status_code, 200)
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal('15'))
        self.assertEqual(bankaccount.balance_initial, Decimal('5'))

    def test_partial_update(self):
        bankaccount = BankAccountFactory(
            label='foo',
            currency='USD',
            owners=[self.user],
        )
        url = reverse('bankaccounts:bankaccount-detail', kwargs={
            'pk': bankaccount.pk,
        })

        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'label': 'bar',
            'currency': 'EUR',
        })
        self.assertEqual(response.status_code, 200)
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.label, 'bar')
        self.assertEqual(bankaccount.currency, 'EUR')


class UpdateViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(user_permissions='all')
        cls.bankaccount = BankAccountFactory(owners=[cls.user])
        cls.url = reverse('bankaccounts:bankaccount-detail', kwargs={
            'pk': cls.bankaccount.pk,
        })

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_authenticated(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_owner_without_permission(self):
        user = UserFactory()
        bankaccount = BankAccountFactory(owners=[user])
        self.client.force_authenticate(user)
        response = self.client.put(
            reverse('bankaccounts:bankaccount-detail', kwargs={
                'pk': bankaccount.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_access_not_owner_with_permissions(self):
        user = UserFactory(user_permissions='all')
        self.client.force_authenticate(user)
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, 404)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(self.url)
        self.assertNotEqual(response.status_code, 403)

    def test_label_required(self):
        bankaccount = BankAccountFactory(owners=[self.user])
        url = reverse('bankaccounts:bankaccount-detail', kwargs={
            'pk': bankaccount.pk,
        })

        self.client.force_authenticate(self.user)
        response = self.client.put(url, data={
            'currency': 'EUR',
            'balance': 10,
            'balance_initial': 10,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('label', response.data)

    def test_currency_required(self):
        bankaccount = BankAccountFactory(owners=[self.user])
        url = reverse('bankaccounts:bankaccount-detail', kwargs={
            'pk': bankaccount.pk,
        })

        self.client.force_authenticate(self.user)
        response = self.client.put(url, data={
            'label': 'foo',
            'balance': 10,
            'balance_initial': 10,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('currency', response.data)

    def test_update(self):
        bankaccount = BankAccountFactory(
            label='foo',
            currency='USD',
            owners=[self.user],
        )
        url = reverse('bankaccounts:bankaccount-detail', kwargs={
            'pk': bankaccount.pk,
        })

        self.client.force_authenticate(self.user)
        response = self.client.put(url, data={
            'label': 'bar',
            'currency': 'EUR',
            'balance': 10,
            'balance_initial': 10,
        })
        self.assertEqual(response.status_code, 200)
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.label, 'bar')
        self.assertEqual(bankaccount.currency, 'EUR')
        self.assertEqual(bankaccount.balance, Decimal('20'))
        self.assertEqual(bankaccount.balance_initial, Decimal('10'))


class DeleteViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(user_permissions='all')
        cls.bankaccount = BankAccountFactory(owners=[cls.user])
        cls.url = reverse('bankaccounts:bankaccount-detail', kwargs={
            'pk': cls.bankaccount.pk,
        })

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_authenticated(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_owner_without_permission(self):
        user = UserFactory()
        bankaccount = BankAccountFactory(owners=[user])
        self.client.force_authenticate(user)
        response = self.client.delete(
            reverse('bankaccounts:bankaccount-detail', kwargs={
                'pk': bankaccount.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_access_not_owner_with_permissions(self):
        user = UserFactory(user_permissions='all')
        self.client.force_authenticate(user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 404)

    def test_access_granted(self):
        bankaccount = BankAccountFactory(owners=[self.user])
        url = reverse('bankaccounts:bankaccount-detail', kwargs={
            'pk': bankaccount.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_delete(self):
        bankaccount = BankAccountFactory(owners=[self.user])
        url = reverse('bankaccounts:bankaccount-detail', kwargs={
            'pk': bankaccount.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(BankAccount.DoesNotExist):
            bankaccount.refresh_from_db()
