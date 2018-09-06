import datetime
import time
from decimal import Decimal
from unittest import mock

from django.test import override_settings

from rest_framework.pagination import PageNumberPagination
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings
from rest_framework.test import APITestCase

from mymoney.bankaccounts import BankAccountFactory
from mymoney.banktransactiontags import BankTransactionTagFactory
from mymoney.api.users.factories import UserFactory

from ..factories import BankTransactionFactory
from ..models import Transaction


class RetrieveViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.bankaccount = BankAccountFactory(currency='USD', owners=[cls.user])
        cls.banktransaction = BankTransactionFactory(bankaccount=cls.bankaccount)
        cls.url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': cls.banktransaction.pk,
        })

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_not_owner(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_retrieve_payment_method(self):
        banktransaction = BankTransactionFactory(
            bankaccount=self.bankaccount,
            payment_method=Transaction.PAYMENT_METHOD_CASH,
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['payment_method_display'],
            banktransaction.get_payment_method_display(),
        )

    def test_retrieve_tag(self):
        tag = BankTransactionTagFactory(name='foo', owner=self.user)
        banktransaction = BankTransactionFactory(
            bankaccount=self.bankaccount,
            tag=tag,
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['tag']['name'], 'foo')

    @override_settings(LANGUAGE_CODE='en-us')
    def test_amount_localize_en_us(self):
        banktransaction = BankTransactionFactory(
            bankaccount=self.bankaccount,
            amount=10,
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['amount_localized'], '+10.00')

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_amount_localize_fr_fr(self):
        banktransaction = BankTransactionFactory(
            bankaccount=self.bankaccount,
            amount=10,
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['amount_localized'], '+10,00')

    @override_settings(LANGUAGE_CODE='en-us')
    def test_amount_currency_en_us(self):
        bankaccount = BankAccountFactory(currency='USD', owners=[self.user])
        banktransaction = BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['amount_currency'], '+$10.00')

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_amount_currency_fr_fr(self):
        bankaccount = BankAccountFactory(currency='EUR', owners=[self.user])
        banktransaction = BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['amount_currency'], '+10,00\xa0€')


class CreateViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(user_permissions='all')
        cls.bankaccount = BankAccountFactory(currency='USD', owners=[cls.user])
        cls.url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': cls.bankaccount.pk,
        })

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_without_permission(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_not_owner_with_permissions(self):
        user = UserFactory(user_permissions='all')
        self.client.force_authenticate(user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url)
        self.assertNotIn(response.status_code, [401, 403])

    def test_label_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'amount': 10,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('label', response.data)

    def test_bankaccount_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
            'bankaccount': BankAccountFactory().pk,
        })
        self.assertEqual(response.status_code, 201)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.bankaccount, self.bankaccount)

    def test_date_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.date, datetime.date.today())

    def test_amount_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('amount', response.data)

    def test_currency_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
            'currency': 'EUR',
        })
        self.assertEqual(response.status_code, 201)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertNotEqual(banktransaction.currency, 'EUR')
        self.assertEqual(banktransaction.currency, self.bankaccount.currency)

    def test_status_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.status, Transaction.STATUS_ACTIVE)

    def test_reconciled_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertFalse(banktransaction.reconciled)

    def test_payment_method_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(
            banktransaction.payment_method,
            Transaction.PAYMENT_METHOD_CREDIT_CARD,
        )

    def test_memo_blank(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.memo, '')

    def test_tag_none(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertIsNone(banktransaction.tag)

    def test_scheduled_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
            'scheduled': True,
        })
        self.assertEqual(response.status_code, 201)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertFalse(banktransaction.scheduled)

    def test_tag_not_owner(self):
        tag = BankTransactionTagFactory()

        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': -10,
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('tag', response.data)

    def test_tag_owner(self):
        tag = BankTransactionTagFactory(owner=self.user)

        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': -10,
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 201)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.tag, tag)

    def test_tag_owner_by_relationship(self):
        user = UserFactory()
        self.bankaccount.owners.add(user)
        tag = BankTransactionTagFactory(owner=user)

        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': -10,
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 201)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.tag, tag)

    def test_create(self):
        tag = BankTransactionTagFactory(owner=self.user)

        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': -10,
            'date': datetime.date(2015, 10, 26),
            'status': Transaction.STATUS_IGNORED,
            'reconciled': True,
            'payment_method': Transaction.PAYMENT_METHOD_CASH,
            'memo': 'blah blah blah',
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 201)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.label, 'foo')
        self.assertEqual(banktransaction.amount, Decimal(-10))
        self.assertEqual(banktransaction.date, datetime.date(2015, 10, 26))
        self.assertEqual(banktransaction.status, Transaction.STATUS_IGNORED)
        self.assertTrue(banktransaction.reconciled)
        self.assertEqual(
            banktransaction.payment_method, Transaction.PAYMENT_METHOD_CASH)
        self.assertEqual(banktransaction.memo, 'blah blah blah')
        self.assertEqual(banktransaction.tag, tag)


class PartialUpdateViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(user_permissions='all')
        cls.bankaccount = BankAccountFactory(currency='EUR', owners=[cls.user])
        cls.banktransaction = BankTransactionFactory(bankaccount=cls.bankaccount)
        cls.url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': cls.banktransaction.pk,
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
        self.bankaccount.owners.add(user)
        banktransaction = BankTransactionFactory()
        self.client.force_authenticate(user)
        response = self.client.patch(
            reverse('banktransactions:banktransaction-detail', kwargs={
                'pk': banktransaction.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_access_not_owner_with_permissions(self):
        user = UserFactory(user_permissions='all')
        self.client.force_authenticate(user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 200)

    def test_update_label(self):
        banktransaction = BankTransactionFactory(
            bankaccount=self.bankaccount,
            label='foo',
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'label': 'bar'
        })
        self.assertEqual(response.status_code, 200)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.label, 'bar')

    def test_bankaccount_not_editable(self):
        banktransaction = BankTransactionFactory(bankaccount=self.bankaccount)
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'bankaccount': BankAccountFactory().pk,
        })
        self.assertEqual(response.status_code, 200)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.bankaccount, self.bankaccount)

    def test_update_date(self):
        banktransaction = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 27),
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'date': datetime.date(2015, 10, 10),
        })
        self.assertEqual(response.status_code, 200)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.date, datetime.date(2015, 10, 10))

    def test_update_status(self):
        banktransaction = BankTransactionFactory(
            bankaccount=self.bankaccount,
            status=Transaction.STATUS_ACTIVE,
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'status': Transaction.STATUS_INACTIVE,
        })
        self.assertEqual(response.status_code, 200)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.status, Transaction.STATUS_INACTIVE)

    def test_currency_not_editable(self):
        banktransaction = BankTransactionFactory(bankaccount=self.bankaccount)
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={'currency': 'USD'})
        self.assertEqual(response.status_code, 200)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.currency, self.bankaccount.currency)

    def test_update_amount_active(self):
        bankaccount = BankAccountFactory(balance=0, owners=[self.user])
        banktransaction = BankTransactionFactory(
            bankaccount=bankaccount,
            amount='10',
            status=Transaction.STATUS_INACTIVE,
        )
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal('0'))

        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'amount': '20',
            'status': Transaction.STATUS_ACTIVE,
        })
        self.assertEqual(response.status_code, 200)

        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.amount, Decimal('20'))

        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal('10'))

    def test_update_amount_inactive(self):
        bankaccount = BankAccountFactory(balance=0, owners=[self.user])
        banktransaction = BankTransactionFactory(
            bankaccount=bankaccount,
            amount='10',
            status=Transaction.STATUS_ACTIVE,
        )
        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal('10'))

        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'amount': '20',
            'status': Transaction.STATUS_INACTIVE,
        })
        self.assertEqual(response.status_code, 200)

        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.amount, Decimal('20'))

        bankaccount.refresh_from_db()
        self.assertEqual(bankaccount.balance, Decimal('10'))

    def test_update_reconciled(self):
        banktransaction = BankTransactionFactory(
            bankaccount=self.bankaccount,
            reconciled=False,
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'reconciled': True,
        })
        self.assertEqual(response.status_code, 200)
        banktransaction.refresh_from_db()
        self.assertTrue(banktransaction.reconciled)

    def test_update_payment_method(self):
        banktransaction = BankTransactionFactory(
            bankaccount=self.bankaccount,
            payment_method=Transaction.PAYMENT_METHOD_CASH,
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'payment_method': Transaction.PAYMENT_METHOD_CHECK,
        })
        self.assertEqual(response.status_code, 200)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.payment_method, Transaction.PAYMENT_METHOD_CHECK)

    def test_update_memo(self):
        banktransaction = BankTransactionFactory(
            bankaccount=self.bankaccount,
            memo='',
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'memo': 'blah blah',
        })
        self.assertEqual(response.status_code, 200)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.memo, 'blah blah')

    def test_add_tag(self):
        tag = BankTransactionTagFactory(owner=self.user)
        banktransaction = BankTransactionFactory(bankaccount=self.bankaccount)
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.tag, tag)

    def test_update_tag(self):
        tag = BankTransactionTagFactory(owner=self.user)
        banktransaction = BankTransactionFactory(
            bankaccount=self.bankaccount,
            tag=BankTransactionTagFactory(owner=self.user),
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(banktransaction.tag, tag)

    def test_remove_tag(self):
        banktransaction = BankTransactionFactory(
            bankaccount=self.bankaccount,
            tag=BankTransactionTagFactory(owner=self.user),
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'tag': None,
        })
        self.assertEqual(response.status_code, 200)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertIsNone(banktransaction.tag)

    def test_update_not_owner_tag(self):
        tag = BankTransactionTagFactory(owner=self.user)
        tag_not_owner = BankTransactionTagFactory()
        banktransaction = BankTransactionFactory(
            bankaccount=self.bankaccount,
            tag=tag,
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'tag': tag_not_owner.pk,
        })
        self.assertEqual(response.status_code, 400)

    def test_scheduled_non_editable(self):
        banktransaction = BankTransactionFactory(
            bankaccount=self.bankaccount,
            scheduled=False,
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'scheduled': True,
        })
        self.assertEqual(response.status_code, 200)
        banktransaction = Transaction.objects.get(pk=response.data['id'])
        self.assertFalse(banktransaction.scheduled)

    def test_partial_update(self):
        tag = BankTransactionTagFactory(owner=self.user)
        banktransaction = BankTransactionFactory(
            bankaccount=self.bankaccount,
            label='foo',
            date=datetime.date(2015, 10, 27),
            amount=0,
            status=Transaction.STATUS_INACTIVE,
            reconciled=False,
            payment_method=Transaction.PAYMENT_METHOD_CREDIT_CARD,
            memo='',
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'label': 'bar',
            'date': datetime.date(2015, 10, 10),
            'amount': 10,
            'status': Transaction.STATUS_ACTIVE,
            'reconciled': True,
            'payment_method': Transaction.PAYMENT_METHOD_CASH,
            'memo': 'blah blah',
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        banktransaction.refresh_from_db()
        self.assertEqual(banktransaction.label, 'bar')
        self.assertEqual(banktransaction.date, datetime.date(2015, 10, 10))
        self.assertEqual(banktransaction.amount, Decimal('10'))
        self.assertEqual(banktransaction.status, Transaction.STATUS_ACTIVE)
        self.assertTrue(banktransaction.reconciled)
        self.assertEqual(banktransaction.payment_method, Transaction.PAYMENT_METHOD_CASH)
        self.assertEqual(banktransaction.memo, 'blah blah')
        self.assertEqual(banktransaction.tag, tag)


class UpdateViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(user_permissions='all')
        cls.bankaccount = BankAccountFactory(owners=[cls.user])
        cls.banktransaction = BankTransactionFactory(bankaccount=cls.bankaccount)
        cls.url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': cls.banktransaction.pk,
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
        self.bankaccount.owners.add(user)
        banktransaction = BankTransactionFactory()
        self.client.force_authenticate(user)
        response = self.client.put(
            reverse('banktransactions:banktransaction-detail', kwargs={
                'pk': banktransaction.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_access_not_owner_with_permissions(self):
        user = UserFactory(user_permissions='all')
        self.client.force_authenticate(user)
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(self.url)
        self.assertNotEqual(response.status_code, 403)

    def test_label_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(self.url, data={
            'amount': 10,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('label', response.data)

    def test_amount_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(self.url, data={
            'label': 'foo',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('amount', response.data)

    def test_update(self):
        tag = BankTransactionTagFactory(owner=self.user)
        banktransaction = BankTransactionFactory(
            bankaccount=self.bankaccount,
            label='foo',
            date=datetime.date(2015, 10, 27),
            amount=0,
            status=Transaction.STATUS_INACTIVE,
            reconciled=False,
            payment_method=Transaction.PAYMENT_METHOD_CREDIT_CARD,
            memo='',
            tag=BankTransactionTagFactory(owner=self.user),
        )
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.put(url, data={
            'label': 'bar',
            'date': datetime.date(2015, 10, 10),
            'amount': 10,
            'status': Transaction.STATUS_ACTIVE,
            'reconciled': True,
            'payment_method': Transaction.PAYMENT_METHOD_CASH,
            'memo': 'blah blah',
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        banktransaction.refresh_from_db()
        self.assertEqual(banktransaction.label, 'bar')
        self.assertEqual(banktransaction.date, datetime.date(2015, 10, 10))
        self.assertEqual(banktransaction.amount, Decimal('10'))
        self.assertEqual(banktransaction.status, Transaction.STATUS_ACTIVE)
        self.assertTrue(banktransaction.reconciled)
        self.assertEqual(banktransaction.payment_method, Transaction.PAYMENT_METHOD_CASH)
        self.assertEqual(banktransaction.memo, 'blah blah')
        self.assertEqual(banktransaction.tag, tag)


class DeleteViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(user_permissions='all')
        cls.bankaccount = BankAccountFactory(owners=[cls.user])
        cls.banktransaction = BankTransactionFactory(bankaccount=cls.bankaccount)
        cls.url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': cls.banktransaction.pk,
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
        self.bankaccount.owners.add(user)
        banktransaction = BankTransactionFactory()
        self.client.force_authenticate(user)
        response = self.client.delete(
            reverse('banktransactions:banktransaction-detail', kwargs={
                'pk': banktransaction.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_access_not_owner_with_permissions(self):
        user = UserFactory(user_permissions='all')
        self.client.force_authenticate(user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_granted(self):
        banktransaction = BankTransactionFactory(bankaccount=self.bankaccount)
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_delete(self):
        banktransaction = BankTransactionFactory(bankaccount=self.bankaccount)
        url = reverse('banktransactions:banktransaction-detail', kwargs={
            'pk': banktransaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(Transaction.DoesNotExist):
            banktransaction.refresh_from_db()


class ListViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.bankaccount = BankAccountFactory(currency='EUR', owners=[cls.user])
        cls.url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': cls.bankaccount.pk,
        })

    def tearDown(self):
        Transaction.objects.all().delete()

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_not_owner(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @mock.patch.object(
        PageNumberPagination, 'page_size', new_callable=mock.PropertyMock)
    def test_pagination(self, size_mock):
        limit = 2
        size_mock.return_value = limit
        total = limit * 2 + 1

        for i in range(0, total):
            BankTransactionFactory(bankaccount=self.bankaccount)

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(total, response.data['count'])
        self.assertFalse(response.data['previous'])
        self.assertIn(self.url + '?page=2', response.data['next'])
        self.assertEqual(len(response.data['results']), limit)

    def test_none(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        self.assertListEqual(response.data['results'], [])

    def test_other_bankaccount(self):
        bt = BankTransactionFactory(bankaccount=self.bankaccount)
        BankTransactionFactory()
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], bt.pk)

    def test_search_icontains(self):
        bt1 = BankTransactionFactory(bankaccount=self.bankaccount, label='foObar')
        bt2 = BankTransactionFactory(bankaccount=self.bankaccount, label='barfOo')
        bt3 = BankTransactionFactory(bankaccount=self.bankaccount, label='foO')
        BankTransactionFactory(bankaccount=self.bankaccount, label='baz')

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            api_settings.SEARCH_PARAM: 'foo',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertListEqual(
            [bt1.pk, bt2.pk, bt3.pk],
            sorted([bt['id'] for bt in response.data['results']]),
        )

    def test_filter_date_start(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 27),
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 26),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 25),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date_0': datetime.date(2015, 10, 26),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertListEqual(
            [bt1.pk, bt2.pk],
            sorted([bt['id'] for bt in response.data['results']]),
        )

    def test_filter_date_end(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 27),
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 26),
        )
        bt3 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 25),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date_1': datetime.date(2015, 10, 26),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertListEqual(
            [bt2.pk, bt3.pk],
            sorted([bt['id'] for bt in response.data['results']]),
        )

    def test_filter_date_ranges(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 26),
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 27),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 28),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date_0': datetime.date(2015, 10, 26),
            'date_1': datetime.date(2015, 10, 27),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertListEqual(
            [bt1.pk, bt2.pk],
            sorted([bt['id'] for bt in response.data['results']]),
        )

    def test_filter_date_invalid(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date_0': 'foo',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('date', response.data)

    def test_filter_date_ranges_invalid(self):
        """
        Start can not be greater than end.
        """
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date_0': datetime.date(2015, 10, 26),
            'date_1': datetime.date(2015, 10, 25),
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(api_settings.NON_FIELD_ERRORS_KEY, response.data)

    def test_filter_amount_min(self):
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            amount=20,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            amount=10,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'amount_0': 15,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], bt.pk)

    def test_filter_amount_max(self):
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            amount=10,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            amount=20,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'amount_1': 15,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], bt.pk)

    def test_filter_amount_ranges(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            amount=10,
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            amount=20,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            amount=0,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            amount=30,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'amount_0': 10,
            'amount_1': 25,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertListEqual(
            [bt1.pk, bt2.pk],
            sorted([bt['id'] for bt in response.data['results']]),
        )

    def test_filter_amount_invalid(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'amount_0': 'foo',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('amount', response.data)

    def test_filter_amount_ranges_invalid(self):
        """
        Min can not be greater than max.
        """
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'amount_0': 20,
            'amount_1': 10,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(api_settings.NON_FIELD_ERRORS_KEY, response.data)

    def test_filter_status(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            status=Transaction.STATUS_ACTIVE,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            status=Transaction.STATUS_INACTIVE,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'status': Transaction.STATUS_ACTIVE,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], bt1.pk)

    def test_filter_status_invalid(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'status': 'foo',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('status', response.data)

    def test_filter_reconciled(self):
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            reconciled=True,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            reconciled=False,
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url, data={
            'reconciled': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], bt.pk)

        response = self.client.get(self.url, data={
            'reconciled': 'True',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], bt.pk)

    def test_filter_unreconciled(self):
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            reconciled=False,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            reconciled=True,
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url, data={
            'reconciled': False,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], bt.pk)

        response = self.client.get(self.url, data={
            'reconciled': 'False',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], bt.pk)

    def test_filter_reconciled_none(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            reconciled=False,
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            reconciled=True,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertListEqual(
            [bt1.pk, bt2.pk],
            sorted([bt['id'] for bt in response.data['results']]),
        )

    def test_filter_reconciled_invalid(self):
        """
        Acts like a None value.
        """
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            reconciled=False,
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            reconciled=True,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'reconciled': 'foo'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertListEqual(
            [bt1.pk, bt2.pk],
            sorted([bt['id'] for bt in response.data['results']]),
        )

    def test_filter_tag_owner(self):
        tag = BankTransactionTagFactory(owner=self.user)
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            tag=tag,
        )
        BankTransactionFactory(bankaccount=self.bankaccount)
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            tag=BankTransactionTagFactory(),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], bt.pk)

    def test_filter_tag_owner_by_relationship(self):
        user = UserFactory()
        self.bankaccount.owners.add(user)
        tag = BankTransactionTagFactory(owner=user)
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            tag=tag,
        )
        BankTransactionFactory(bankaccount=self.bankaccount)
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            tag=BankTransactionTagFactory(),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], bt.pk)

    def test_filter_tag_multiple(self):
        tag1 = BankTransactionTagFactory(owner=self.user)
        tag2 = BankTransactionTagFactory(owner=self.user)
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            tag=tag1,
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            tag=tag2,
        )
        BankTransactionFactory(bankaccount=self.bankaccount)
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            tag=BankTransactionTagFactory(),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'tag': [tag1.pk, tag2.pk]
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertListEqual(
            [bt1.pk, bt2.pk],
            sorted([bt['id'] for bt in response.data['results']]),
        )

    def test_filter_tag_not_owner(self):
        tag = BankTransactionTagFactory()
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 400)

    def test_ordering_default(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 25),
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 27),
        )
        bt3 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 26),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertListEqual(
            [bt2.pk, bt3.pk, bt1.pk],
            [bt['id'] for bt in response.data['results']],
        )

    def test_ordering_label_asc(self):
        bt1 = BankTransactionFactory(
            label='foo',
            bankaccount=self.bankaccount,
        )
        bt2 = BankTransactionFactory(
            label='bar',
            bankaccount=self.bankaccount,
        )
        bt3 = BankTransactionFactory(
            label='baz',
            bankaccount=self.bankaccount,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            '{key}'.format(key=api_settings.ORDERING_PARAM): 'label',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertListEqual(
            [bt2.pk, bt3.pk, bt1.pk],
            [bt['id'] for bt in response.data['results']],
        )

    def test_ordering_label_desc(self):
        bt1 = BankTransactionFactory(
            label='bar',
            bankaccount=self.bankaccount,
        )
        bt2 = BankTransactionFactory(
            label='foo',
            bankaccount=self.bankaccount,
        )
        bt3 = BankTransactionFactory(
            label='baz',
            bankaccount=self.bankaccount,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            '{key}'.format(key=api_settings.ORDERING_PARAM): '-label',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertListEqual(
            [bt2.pk, bt3.pk, bt1.pk],
            [bt['id'] for bt in response.data['results']],
        )

    def test_ordering_date_asc(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 27),
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 25),
        )
        bt3 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 26),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            '{key}'.format(key=api_settings.ORDERING_PARAM): 'date',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertListEqual(
            [bt2.pk, bt3.pk, bt1.pk],
            [bt['id'] for bt in response.data['results']],
        )

    def test_ordering_date_desc(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 25),
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 27),
        )
        bt3 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 26),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            '{key}'.format(key=api_settings.ORDERING_PARAM): '-date',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertListEqual(
            [bt2.pk, bt3.pk, bt1.pk],
            [bt['id'] for bt in response.data['results']],
        )

    def test_ordering_label_conflict_by_id_desc(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            label='foo',
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            label='foo',
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            '{key}'.format(key=api_settings.ORDERING_PARAM): 'label',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertListEqual(
            [bt2.pk, bt1.pk],
            [bt['id'] for bt in response.data['results']],
        )

    def test_ordering_date_conflict_by_id_desc(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 27),
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 27),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            '{key}'.format(key=api_settings.ORDERING_PARAM): 'date',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertListEqual(
            [bt2.pk, bt1.pk],
            [bt['id'] for bt in response.data['results']],
        )

    def test_balance_total_other_bankaccount(self):
        bankaccount = BankAccountFactory(balance_initial=0, owners=[self.user])
        url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
            date=datetime.date(2015, 10, 29),
        )
        BankTransactionFactory(
            amount=10,
            date=datetime.date(2015, 10, 28),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['balance_total'], '10.00')

    def test_balance_total_no_initial_balance(self):
        bankaccount = BankAccountFactory(balance_initial=0, owners=[self.user])
        url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
            date=datetime.date(2015, 10, 29),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['balance_total'], '10.00')

    def test_balance_total_initial_balance(self):
        bankaccount = BankAccountFactory(balance_initial=15, owners=[self.user])
        url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
            date=datetime.date(2015, 10, 29),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['balance_total'], '25.00')

    def test_balance_total_same_day(self):
        bankaccount = BankAccountFactory(balance_initial=0, owners=[self.user])
        url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
            date=datetime.date(2015, 10, 29),
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
            date=datetime.date(2015, 10, 29),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['balance_total'], '20.00')
        self.assertEqual(response.data['results'][1]['balance_total'], '10.00')

    def test_balance_total_next_day(self):
        bankaccount = BankAccountFactory(balance_initial=0, owners=[self.user])
        url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
            date=datetime.date(2015, 10, 27),
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=20,
            date=datetime.date(2015, 10, 28),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][1]['balance_total'], '10.00')

    def test_balance_total(self):
        bankaccount = BankAccountFactory(balance_initial=0, owners=[self.user])
        url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
            date=datetime.date(2015, 10, 27),
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=15,
            date=datetime.date(2015, 10, 28),
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=30,
            date=datetime.date(2015, 10, 29),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(response.data['results'][0]['balance_total'], '55.00')
        self.assertEqual(response.data['results'][1]['balance_total'], '25.00')
        self.assertEqual(response.data['results'][2]['balance_total'], '10.00')

    def test_balance_reconciled_none_reconciled(self):
        bankaccount = BankAccountFactory(balance_initial=0, owners=[self.user])
        url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })
        BankTransactionFactory(
            bankaccount=bankaccount,
            reconciled=False,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertIsNone(response.data['results'][0]['balance_reconciled'])

    def test_balance_reconciled_other_bankaccount(self):
        bankaccount = BankAccountFactory(balance_initial=0, owners=[self.user])
        url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })
        BankTransactionFactory(
            bankaccount=bankaccount,
            reconciled=True,
            amount=10,
        )
        BankTransactionFactory(
            reconciled=True,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['balance_reconciled'], '10.00')

    def test_balance_reconciled_not_all_reconciled(self):
        bankaccount = BankAccountFactory(balance_initial=0, owners=[self.user])
        url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })
        BankTransactionFactory(
            bankaccount=bankaccount,
            reconciled=True,
            amount=10,
            date=datetime.date(2015, 10, 28),
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            reconciled=False,
            amount=10,
            date=datetime.date(2015, 10, 29),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['balance_reconciled'], '10.00')
        self.assertEqual(response.data['results'][1]['balance_reconciled'], '10.00')

    def test_balance_reconciled_no_initial_balance(self):
        bankaccount = BankAccountFactory(balance_initial=0, owners=[self.user])
        url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })
        BankTransactionFactory(
            bankaccount=bankaccount,
            reconciled=True,
            amount=10,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['balance_reconciled'], '10.00')

    def test_balance_reconciled_initial_balance(self):
        bankaccount = BankAccountFactory(balance_initial=10, owners=[self.user])
        url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })
        BankTransactionFactory(
            bankaccount=bankaccount,
            reconciled=True,
            amount=10,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['balance_reconciled'], '20.00')

    def test_balance_reconciled_same_day(self):
        bankaccount = BankAccountFactory(balance_initial=0, owners=[self.user])
        url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })
        BankTransactionFactory(
            bankaccount=bankaccount,
            reconciled=True,
            amount=10,
            date=datetime.date(2015, 10, 29),
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            reconciled=True,
            amount=10,
            date=datetime.date(2015, 10, 29),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['balance_reconciled'], '20.00')
        self.assertEqual(response.data['results'][1]['balance_reconciled'], '10.00')

    def test_balance_reconciled_next_day(self):
        bankaccount = BankAccountFactory(balance_initial=0, owners=[self.user])
        url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })
        BankTransactionFactory(
            bankaccount=bankaccount,
            reconciled=True,
            amount=10,
            date=datetime.date(2015, 10, 29),
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            reconciled=True,
            amount=10,
            date=datetime.date(2015, 10, 28),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][1]['balance_reconciled'], '10.00')

    def test_balance_reconciled(self):
        bankaccount = BankAccountFactory(balance_initial=0, owners=[self.user])
        url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })
        BankTransactionFactory(
            bankaccount=bankaccount,
            reconciled=True,
            amount=10,
            date=datetime.date(2015, 10, 27),
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            reconciled=True,
            amount=15,
            date=datetime.date(2015, 10, 28),
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            reconciled=False,
            amount=30,
            date=datetime.date(2015, 10, 29),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(response.data['results'][0]['balance_reconciled'], '25.00')
        self.assertEqual(response.data['results'][1]['balance_reconciled'], '25.00')
        self.assertEqual(response.data['results'][2]['balance_reconciled'], '10.00')


class PartialUpdateMultipleViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(user_permissions='all')
        cls.bankaccount = BankAccountFactory(currency='EUR', owners=[cls.user])
        cls.url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': cls.bankaccount.pk,
        })

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_not_owner_without_permission(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_owner_without_permission(self):
        user = UserFactory()
        self.bankaccount.owners.add(user)
        self.client.force_authenticate(user)
        response = self.client.patch(
            reverse('banktransactions:banktransaction-list', kwargs={
                'bankaccount_pk': self.bankaccount.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_access_not_owner_with_permissions(self):
        user = UserFactory(user_permissions='all')
        self.client.force_authenticate(user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url)
        self.assertNotEqual(response.status_code, 403)

    def test_missing_ids(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 400)

    def test_unknown_all_ids(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={'ids': [-1]})
        self.assertEqual(response.status_code, 400)

    def test_unknown_some_ids(self):
        bt = BankTransactionFactory(bankaccount=self.bankaccount)
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [-1, bt.pk],
        })
        self.assertEqual(response.status_code, 400)

    def test_not_owner_all_ids(self):
        bt = BankTransactionFactory()
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
        })
        self.assertEqual(response.status_code, 400)

    def test_not_owner_some_ids(self):
        bt1 = BankTransactionFactory(bankaccount=self.bankaccount)
        bt2 = BankTransactionFactory()
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt1.pk, bt2.pk],
        })
        self.assertEqual(response.status_code, 400)

    def test_invalid_reconciled(self):
        bt = BankTransactionFactory(bankaccount=self.bankaccount)
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
            'reconciled': 'foo'
        })
        self.assertEqual(response.status_code, 400)

    def test_invalid_status(self):
        bt = BankTransactionFactory(bankaccount=self.bankaccount)
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
            'status': 'foo'
        })
        self.assertEqual(response.status_code, 400)

    def test_update_multiple_no_field(self):
        bt = BankTransactionFactory(bankaccount=self.bankaccount)

        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
        })
        self.assertEqual(response.status_code, 200)

    def test_update_multiple_field_not_allowed(self):
        bt = BankTransactionFactory(bankaccount=self.bankaccount, amount=20)

        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
            'amount': 10,
        })
        self.assertEqual(response.status_code, 200)
        bt.refresh_from_db()
        self.assertEqual(bt.amount, Decimal('20'))

    def test_update_multiple_reconciled_boolean(self):
        bt1 = BankTransactionFactory(bankaccount=self.bankaccount, reconciled=True)
        bt2 = BankTransactionFactory(bankaccount=self.bankaccount, reconciled=False)

        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt1.pk, bt2.pk],
            'reconciled': True,
        })
        self.assertEqual(response.status_code, 200)
        bt1.refresh_from_db()
        bt2.refresh_from_db()
        self.assertTrue(bt1.reconciled)
        self.assertTrue(bt2.reconciled)

    def test_update_multiple_reconciled_integer(self):
        bt = BankTransactionFactory(bankaccount=self.bankaccount, reconciled=False)
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
            'reconciled': 1,
        })
        self.assertEqual(response.status_code, 200)
        bt.refresh_from_db()
        self.assertTrue(bt.reconciled)

    def test_update_multiple_reconciled_string(self):
        bt = BankTransactionFactory(bankaccount=self.bankaccount, reconciled=False)
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
            'reconciled': 'true',
        })
        self.assertEqual(response.status_code, 200)
        bt.refresh_from_db()
        self.assertTrue(bt.reconciled)

    def test_update_multiple_unreconciled_boolean(self):
        bt1 = BankTransactionFactory(bankaccount=self.bankaccount, reconciled=True)
        bt2 = BankTransactionFactory(bankaccount=self.bankaccount, reconciled=False)

        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt1.pk, bt2.pk],
            'reconciled': False,
        })
        self.assertEqual(response.status_code, 200)
        bt1.refresh_from_db()
        bt2.refresh_from_db()
        self.assertFalse(bt1.reconciled)
        self.assertFalse(bt2.reconciled)

    def test_update_multiple_unreconciled_integer(self):
        bt = BankTransactionFactory(bankaccount=self.bankaccount, reconciled=True)
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
            'reconciled': 0,
        })
        self.assertEqual(response.status_code, 200)
        bt.refresh_from_db()
        self.assertFalse(bt.reconciled)

    def test_update_multiple_unreconciled_string(self):
        bt = BankTransactionFactory(bankaccount=self.bankaccount, reconciled=True)
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
            'reconciled': "false",
        })
        self.assertEqual(response.status_code, 200)
        bt.refresh_from_db()
        self.assertFalse(bt.reconciled)

    def test_update_multiple_status(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            status=Transaction.STATUS_INACTIVE,
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            status=Transaction.STATUS_ACTIVE,
        )

        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt1.pk, bt2.pk],
            'status': Transaction.STATUS_ACTIVE,
        })
        self.assertEqual(response.status_code, 200)
        bt1.refresh_from_db()
        bt2.refresh_from_db()
        self.assertEqual(bt1.status, Transaction.STATUS_ACTIVE)
        self.assertEqual(bt2.status, Transaction.STATUS_ACTIVE)


class DeleteMultipleViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(user_permissions='all')
        cls.bankaccount = BankAccountFactory(currency='EUR', owners=[cls.user])
        cls.url = reverse('banktransactions:banktransaction-list', kwargs={
            'bankaccount_pk': cls.bankaccount.pk,
        })

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_not_owner_without_permission(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_owner_without_permission(self):
        user = UserFactory()
        self.bankaccount.owners.add(user)
        self.client.force_authenticate(user)
        response = self.client.delete(
            reverse('banktransactions:banktransaction-list', kwargs={
                'bankaccount_pk': self.bankaccount.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_access_not_owner_with_permissions(self):
        user = UserFactory(user_permissions='all')
        self.client.force_authenticate(user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url)
        self.assertNotEqual(response.status_code, 403)

    def test_missing_ids(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 400)

    def test_unknown_all_ids(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url, data={'ids': [-1]})
        self.assertEqual(response.status_code, 400)

    def test_unknown_some_ids(self):
        bt = BankTransactionFactory(bankaccount=self.bankaccount)
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url, data={
            'ids': [-1, bt.pk],
        })
        self.assertEqual(response.status_code, 400)

    def test_not_owner_all_ids(self):
        bt = BankTransactionFactory()
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url, data={
            'ids': [bt.pk],
        })
        self.assertEqual(response.status_code, 400)

    def test_not_owner_some_ids(self):
        bt1 = BankTransactionFactory(bankaccount=self.bankaccount)
        bt2 = BankTransactionFactory()
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url, data={
            'ids': [bt1.pk, bt2.pk],
        })
        self.assertEqual(response.status_code, 400)

    def test_delete_multiple(self):
        bt1 = BankTransactionFactory(bankaccount=self.bankaccount)
        bt2 = BankTransactionFactory(bankaccount=self.bankaccount)

        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url, data={
            'ids': [bt1.pk, bt2.pk],
        })
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(Transaction.DoesNotExist):
            bt1.refresh_from_db()
        with self.assertRaises(Transaction.DoesNotExist):
            bt2.refresh_from_db()


class CalendarEventsViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.bankaccount = BankAccountFactory(currency='EUR', owners=[cls.user])
        cls.url = reverse('banktransactions:banktransaction-calendar-events', kwargs={
            'bankaccount_pk': cls.bankaccount.pk,
        })

    def tearDown(self):
        Transaction.objects.all().delete()

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_not_owner(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 403)

    def test_dates_missing(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)

    def test_date_from_missing(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={"to": "1446073200000"})
        self.assertEqual(response.status_code, 400)

    def test_date_to_missing(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={"from": "1446073200000"})
        self.assertEqual(response.status_code, 400)

    def test_date_from_invalid(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={"from": "foo"})
        self.assertEqual(response.status_code, 400)

    def test_date_to_invalid(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={"to": "foo"})
        self.assertEqual(response.status_code, 400)

    def test_date_ranges_invalid(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            "from": int(time.mktime(datetime.date(2015, 10, 30).timetuple())) * 1000,
            "to": int(time.mktime(datetime.date(2015, 10, 29).timetuple())) * 1000,
        })
        self.assertEqual(response.status_code, 400)

    def test_none(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={"to": "foo"})
        self.assertEqual(response.status_code, 400)

    def test_out_of_ranges_before(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 29),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 28),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            "from": int(time.mktime(datetime.date(2015, 10, 25).timetuple())) * 1000,
            "to": int(time.mktime(datetime.date(2015, 10, 27).timetuple())) * 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['result'])

    def test_out_of_ranges_after(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 29),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 28),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            "from": int(time.mktime(datetime.date(2015, 10, 30).timetuple())) * 1000,
            "to": int(time.mktime(datetime.date(2015, 10, 31).timetuple())) * 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['result'])

    def test_other_bankaccount(self):
        BankTransactionFactory(
            date=datetime.date(2015, 10, 29),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            "from": int(time.mktime(datetime.date(2015, 10, 28).timetuple())) * 1000,
            "to": int(time.mktime(datetime.date(2015, 10, 31).timetuple())) * 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['result'])

    def test_same_day(self):
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 29),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 30),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            "from": int(time.mktime(datetime.date(2015, 10, 29).timetuple())) * 1000,
            "to": int(time.mktime(datetime.date(2015, 10, 29).timetuple())) * 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['result']), 1)
        self.assertEqual(response.data['result'][0]['id'], bt.pk)

    def test_order_date(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 29),
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 30),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            "from": int(time.mktime(datetime.date(2015, 10, 28).timetuple())) * 1000,
            "to": int(time.mktime(datetime.date(2015, 10, 31).timetuple())) * 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['result']), 2)
        self.assertEqual(response.data['result'][0]['id'], bt1.pk)
        self.assertEqual(response.data['result'][1]['id'], bt2.pk)

    def test_order_date_conflict(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 29),
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 29),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            "from": int(time.mktime(datetime.date(2015, 10, 28).timetuple())) * 1000,
            "to": int(time.mktime(datetime.date(2015, 10, 31).timetuple())) * 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['result']), 2)
        self.assertEqual(response.data['result'][0]['id'], bt1.pk)
        self.assertEqual(response.data['result'][1]['id'], bt2.pk)

    def test_balance_total(self):
        bankaccount = BankAccountFactory(owners=[self.user])
        url = reverse('banktransactions:banktransaction-calendar-events', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })

        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
            date=datetime.date(2015, 10, 29),
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
            date=datetime.date(2015, 10, 30),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(url, data={
            "from": int(time.mktime(datetime.date(2015, 10, 28).timetuple())) * 1000,
            "to": int(time.mktime(datetime.date(2015, 10, 31).timetuple())) * 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['result']), 2)
        self.assertEqual(
            response.data['result'][0]['extra_data']['balance_total'],
            Decimal(10),
        )
        self.assertEqual(
            response.data['result'][1]['extra_data']['balance_total'],
            Decimal(20),
        )

    def test_balance_reconciled(self):
        bankaccount = BankAccountFactory(owners=[self.user])
        url = reverse('banktransactions:banktransaction-calendar-events', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })

        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
            date=datetime.date(2015, 10, 29),
            reconciled=False,
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
            date=datetime.date(2015, 10, 30),
            reconciled=True,
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            amount=10,
            date=datetime.date(2015, 10, 31),
            reconciled=True,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(url, data={
            "from": int(time.mktime(datetime.date(2015, 10, 28).timetuple())) * 1000,
            "to": int(time.mktime(datetime.date(2015, 11, 1).timetuple())) * 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['result']), 3)
        self.assertIsNone(response.data['result'][0]['extra_data']['balance_reconciled'])
        self.assertEqual(
            response.data['result'][1]['extra_data']['balance_reconciled'],
            Decimal(10),
        )
        self.assertEqual(
            response.data['result'][2]['extra_data']['balance_reconciled'],
            Decimal(20),
        )

    def test_response(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 29),
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 30),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            "from": int(time.mktime(datetime.date(2015, 10, 28).timetuple())) * 1000,
            "to": int(time.mktime(datetime.date(2015, 10, 31).timetuple())) * 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['success'], 1)
        self.assertEqual(len(response.data['result']), 2)
        self.assertEqual(response.data['result'][0]['id'], bt1.pk)
        self.assertEqual(response.data['result'][1]['id'], bt2.pk)
