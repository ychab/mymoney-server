import datetime
from decimal import Decimal
from unittest import mock

from django.test import override_settings

from rest_framework.pagination import PageNumberPagination
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings
from rest_framework.test import APITestCase

from mymoney.accounts.factories import AccountFactory
from mymoney.core.factories import UserFactory
from mymoney.tags.factories import TagFactory

from ..factories import TransactionFactory
from ..models import Transaction


class RetrieveViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.account = AccountFactory(currency='USD')
        cls.transaction = TransactionFactory(account=cls.account)
        cls.url = reverse('transaction-detail', kwargs={
            'pk': cls.transaction.pk,
        })

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_retrieve_payment_method(self):
        transaction = TransactionFactory(
            account=self.account,
            payment_method=Transaction.PAYMENT_METHOD_CASH,
        )
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['payment_method_display'],
            transaction.get_payment_method_display(),
        )

    def test_retrieve_tag(self):
        tag = TagFactory(name='foo')
        transaction = TransactionFactory(
            account=self.account,
            tag=tag,
        )
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['tag']['name'], 'foo')

    @override_settings(LANGUAGE_CODE='en-us')
    def test_amount_localize_en_us(self):
        transaction = TransactionFactory(
            account=self.account,
            amount=10,
        )
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['amount_localized'], '+10.00')

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_amount_localize_fr_fr(self):
        transaction = TransactionFactory(
            account=self.account,
            amount=10,
        )
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['amount_localized'], '+10,00')

    @override_settings(LANGUAGE_CODE='en-us')
    def test_amount_currency_en_us(self):
        account = AccountFactory(currency='USD')
        transaction = TransactionFactory(
            account=account,
            amount=10,
        )
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['amount_currency'], '+$10.00')

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_amount_currency_fr_fr(self):
        account = AccountFactory(currency='EUR')
        transaction = TransactionFactory(
            account=account,
            amount=10,
        )
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['amount_currency'], '+10,00\xa0€')


class CreateViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.account = AccountFactory(currency='USD')
        cls.url = reverse('transaction-list')

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

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

    def test_account_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
            'account': AccountFactory().pk,
        })
        self.assertEqual(response.status_code, 201)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(transaction.account, self.account)

    def test_date_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(transaction.date, datetime.date.today())

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
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertNotEqual(transaction.currency, 'EUR')
        self.assertEqual(transaction.currency, self.account.currency)

    def test_status_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(transaction.status, Transaction.STATUS_ACTIVE)

    def test_reconciled_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertFalse(transaction.reconciled)

    def test_payment_method_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(
            transaction.payment_method,
            Transaction.PAYMENT_METHOD_CREDIT_CARD,
        )

    def test_memo_blank(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(transaction.memo, '')

    def test_tag_none(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertIsNone(transaction.tag)

    def test_scheduled_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
            'scheduled': True,
        })
        self.assertEqual(response.status_code, 201)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertFalse(transaction.scheduled)

    def test_create(self):
        tag = TagFactory()

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
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(transaction.label, 'foo')
        self.assertEqual(transaction.amount, Decimal(-10))
        self.assertEqual(transaction.date, datetime.date(2015, 10, 26))
        self.assertEqual(transaction.status, Transaction.STATUS_IGNORED)
        self.assertTrue(transaction.reconciled)
        self.assertEqual(
            transaction.payment_method, Transaction.PAYMENT_METHOD_CASH)
        self.assertEqual(transaction.memo, 'blah blah blah')
        self.assertEqual(transaction.tag, tag)


class PartialUpdateViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.account = AccountFactory(currency='EUR')
        cls.transaction = TransactionFactory(account=cls.account)
        cls.url = reverse('transaction-detail', kwargs={
            'pk': cls.transaction.pk,
        })

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 401)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 200)

    def test_update_label(self):
        transaction = TransactionFactory(
            account=self.account,
            label='foo',
        )
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'label': 'bar'
        })
        self.assertEqual(response.status_code, 200)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(transaction.label, 'bar')

    def test_account_not_editable(self):
        transaction = TransactionFactory(account=self.account)
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'account': AccountFactory().pk,
        })
        self.assertEqual(response.status_code, 200)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(transaction.account, self.account)

    def test_update_date(self):
        transaction = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 10, 27),
        )
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'date': datetime.date(2015, 10, 10),
        })
        self.assertEqual(response.status_code, 200)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(transaction.date, datetime.date(2015, 10, 10))

    def test_update_status(self):
        transaction = TransactionFactory(
            account=self.account,
            status=Transaction.STATUS_ACTIVE,
        )
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'status': Transaction.STATUS_INACTIVE,
        })
        self.assertEqual(response.status_code, 200)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(transaction.status, Transaction.STATUS_INACTIVE)

    def test_currency_not_editable(self):
        transaction = TransactionFactory(account=self.account)
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={'currency': 'USD'})
        self.assertEqual(response.status_code, 200)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(transaction.currency, self.account.currency)

    def test_update_amount_active(self):
        self.account.balance = 0
        self.account.save()

        transaction = TransactionFactory(
            account=self.account,
            amount='10',
            status=Transaction.STATUS_INACTIVE,
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('0'))

        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'amount': '20',
            'status': Transaction.STATUS_ACTIVE,
        })
        self.assertEqual(response.status_code, 200)

        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(transaction.amount, Decimal('20'))

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('10'))

    def test_update_amount_inactive(self):
        account = AccountFactory(balance=0)
        transaction = TransactionFactory(
            account=account,
            amount='10',
            status=Transaction.STATUS_ACTIVE,
        )
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('10'))

        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'amount': '20',
            'status': Transaction.STATUS_INACTIVE,
        })
        self.assertEqual(response.status_code, 200)

        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(transaction.amount, Decimal('20'))

        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('10'))

    def test_update_reconciled(self):
        transaction = TransactionFactory(
            account=self.account,
            reconciled=False,
        )
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'reconciled': True,
        })
        self.assertEqual(response.status_code, 200)
        transaction.refresh_from_db()
        self.assertTrue(transaction.reconciled)

    def test_update_payment_method(self):
        transaction = TransactionFactory(
            account=self.account,
            payment_method=Transaction.PAYMENT_METHOD_CASH,
        )
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'payment_method': Transaction.PAYMENT_METHOD_CHECK,
        })
        self.assertEqual(response.status_code, 200)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(transaction.payment_method, Transaction.PAYMENT_METHOD_CHECK)

    def test_update_memo(self):
        transaction = TransactionFactory(
            account=self.account,
            memo='',
        )
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'memo': 'blah blah',
        })
        self.assertEqual(response.status_code, 200)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(transaction.memo, 'blah blah')

    def test_add_tag(self):
        tag = TagFactory()
        transaction = TransactionFactory(account=self.account)
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(transaction.tag, tag)

    def test_update_tag(self):
        tag = TagFactory()
        transaction = TransactionFactory(
            account=self.account,
            tag=TagFactory(),
        )
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertEqual(transaction.tag, tag)

    def test_remove_tag(self):
        transaction = TransactionFactory(
            account=self.account,
            tag=TagFactory(),
        )
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'tag': None,
        })
        self.assertEqual(response.status_code, 200)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertIsNone(transaction.tag)

    def test_scheduled_non_editable(self):
        transaction = TransactionFactory(
            account=self.account,
            scheduled=False,
        )
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'scheduled': True,
        })
        self.assertEqual(response.status_code, 200)
        transaction = Transaction.objects.get(pk=response.data['id'])
        self.assertFalse(transaction.scheduled)

    def test_partial_update(self):
        tag = TagFactory()
        transaction = TransactionFactory(
            account=self.account,
            label='foo',
            date=datetime.date(2015, 10, 27),
            amount=0,
            status=Transaction.STATUS_INACTIVE,
            reconciled=False,
            payment_method=Transaction.PAYMENT_METHOD_CREDIT_CARD,
            memo='',
        )
        url = reverse('transaction-detail', kwargs={
            'pk': transaction.pk,
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
        transaction.refresh_from_db()
        self.assertEqual(transaction.label, 'bar')
        self.assertEqual(transaction.date, datetime.date(2015, 10, 10))
        self.assertEqual(transaction.amount, Decimal('10'))
        self.assertEqual(transaction.status, Transaction.STATUS_ACTIVE)
        self.assertTrue(transaction.reconciled)
        self.assertEqual(transaction.payment_method, Transaction.PAYMENT_METHOD_CASH)
        self.assertEqual(transaction.memo, 'blah blah')
        self.assertEqual(transaction.tag, tag)


class DeleteViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.account = AccountFactory()
        cls.transaction = TransactionFactory(account=cls.account)
        cls.url = reverse('transaction-detail', kwargs={
            'pk': cls.transaction.pk,
        })

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 401)

    def test_delete(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(Transaction.DoesNotExist):
            self.transaction.refresh_from_db()


class ListViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.account = AccountFactory(currency='EUR')
        cls.url = reverse('transaction-list')

    def tearDown(self):
        Transaction.objects.all().delete()

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

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
            TransactionFactory(account=self.account)

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
        bt = TransactionFactory(account=self.account)
        TransactionFactory(account=AccountFactory())
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], bt.pk)

    def test_search_icontains(self):
        bt1 = TransactionFactory(account=self.account, label='foObar')
        bt2 = TransactionFactory(account=self.account, label='barfOo')
        bt3 = TransactionFactory(account=self.account, label='foO')
        TransactionFactory(account=self.account, label='baz')

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
        bt1 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 10, 27),
        )
        bt2 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 10, 26),
        )
        TransactionFactory(
            account=self.account,
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
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 10, 27),
        )
        bt2 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 10, 26),
        )
        bt3 = TransactionFactory(
            account=self.account,
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
        bt1 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 10, 26),
        )
        bt2 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 10, 27),
        )
        TransactionFactory(
            account=self.account,
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
        bt = TransactionFactory(
            account=self.account,
            amount=20,
        )
        TransactionFactory(
            account=self.account,
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
        bt = TransactionFactory(
            account=self.account,
            amount=10,
        )
        TransactionFactory(
            account=self.account,
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
        bt1 = TransactionFactory(
            account=self.account,
            amount=10,
        )
        bt2 = TransactionFactory(
            account=self.account,
            amount=20,
        )
        TransactionFactory(
            account=self.account,
            amount=0,
        )
        TransactionFactory(
            account=self.account,
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
        bt1 = TransactionFactory(
            account=self.account,
            status=Transaction.STATUS_ACTIVE,
        )
        TransactionFactory(
            account=self.account,
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
        bt = TransactionFactory(
            account=self.account,
            reconciled=True,
        )
        TransactionFactory(
            account=self.account,
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
        bt = TransactionFactory(
            account=self.account,
            reconciled=False,
        )
        TransactionFactory(
            account=self.account,
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
        bt1 = TransactionFactory(
            account=self.account,
            reconciled=False,
        )
        bt2 = TransactionFactory(
            account=self.account,
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
        bt1 = TransactionFactory(
            account=self.account,
            reconciled=False,
        )
        bt2 = TransactionFactory(
            account=self.account,
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

    def test_filter_tag(self):
        tag = TagFactory()
        bt = TransactionFactory(
            account=self.account,
            tag=tag,
        )
        TransactionFactory(account=self.account)
        TransactionFactory(
            account=self.account,
            tag=TagFactory(),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], bt.pk)

    def test_filter_tag_multiple(self):
        tag1 = TagFactory()
        tag2 = TagFactory()
        bt1 = TransactionFactory(
            account=self.account,
            tag=tag1,
        )
        bt2 = TransactionFactory(
            account=self.account,
            tag=tag2,
        )
        TransactionFactory(account=self.account)
        TransactionFactory(
            account=self.account,
            tag=TagFactory(),
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

    def test_ordering_default(self):
        bt1 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 10, 25),
        )
        bt2 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 10, 27),
        )
        bt3 = TransactionFactory(
            account=self.account,
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
        bt1 = TransactionFactory(
            label='foo',
            account=self.account,
        )
        bt2 = TransactionFactory(
            label='bar',
            account=self.account,
        )
        bt3 = TransactionFactory(
            label='baz',
            account=self.account,
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
        bt1 = TransactionFactory(
            label='bar',
            account=self.account,
        )
        bt2 = TransactionFactory(
            label='foo',
            account=self.account,
        )
        bt3 = TransactionFactory(
            label='baz',
            account=self.account,
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
        bt1 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 10, 27),
        )
        bt2 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 10, 25),
        )
        bt3 = TransactionFactory(
            account=self.account,
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
        bt1 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 10, 25),
        )
        bt2 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 10, 27),
        )
        bt3 = TransactionFactory(
            account=self.account,
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
        bt1 = TransactionFactory(
            account=self.account,
            label='foo',
        )
        bt2 = TransactionFactory(
            account=self.account,
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
        bt1 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 10, 27),
        )
        bt2 = TransactionFactory(
            account=self.account,
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

    def test_balance_total_same_day(self):
        TransactionFactory(
            account=self.account,
            amount=10,
            date=datetime.date(2015, 10, 29),
        )
        TransactionFactory(
            account=self.account,
            amount=10,
            date=datetime.date(2015, 10, 29),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['balance_total'], '20.00')
        self.assertEqual(response.data['results'][1]['balance_total'], '10.00')

    def test_balance_total_next_day(self):
        TransactionFactory(
            account=self.account,
            amount=10,
            date=datetime.date(2015, 10, 27),
        )
        TransactionFactory(
            account=self.account,
            amount=20,
            date=datetime.date(2015, 10, 28),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][1]['balance_total'], '10.00')

    def test_balance_total(self):
        TransactionFactory(
            account=self.account,
            amount=10,
            date=datetime.date(2015, 10, 27),
        )
        TransactionFactory(
            account=self.account,
            amount=15,
            date=datetime.date(2015, 10, 28),
        )
        TransactionFactory(
            account=self.account,
            amount=30,
            date=datetime.date(2015, 10, 29),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(response.data['results'][0]['balance_total'], '55.00')
        self.assertEqual(response.data['results'][1]['balance_total'], '25.00')
        self.assertEqual(response.data['results'][2]['balance_total'], '10.00')

    def test_balance_reconciled_none_reconciled(self):
        TransactionFactory(
            account=self.account,
            reconciled=False,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertIsNone(response.data['results'][0]['balance_reconciled'])

    def test_balance_reconciled_not_all_reconciled(self):
        TransactionFactory(
            account=self.account,
            reconciled=True,
            amount=10,
            date=datetime.date(2015, 10, 28),
        )
        TransactionFactory(
            account=self.account,
            reconciled=False,
            amount=10,
            date=datetime.date(2015, 10, 29),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['balance_reconciled'], '10.00')
        self.assertEqual(response.data['results'][1]['balance_reconciled'], '10.00')

    def test_balance_reconciled_same_day(self):
        TransactionFactory(
            account=self.account,
            reconciled=True,
            amount=10,
            date=datetime.date(2015, 10, 29),
        )
        TransactionFactory(
            account=self.account,
            reconciled=True,
            amount=10,
            date=datetime.date(2015, 10, 29),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['balance_reconciled'], '20.00')
        self.assertEqual(response.data['results'][1]['balance_reconciled'], '10.00')

    def test_balance_reconciled_next_day(self):
        TransactionFactory(
            account=self.account,
            reconciled=True,
            amount=10,
            date=datetime.date(2015, 10, 29),
        )
        TransactionFactory(
            account=self.account,
            reconciled=True,
            amount=10,
            date=datetime.date(2015, 10, 28),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][1]['balance_reconciled'], '10.00')

    def test_balance_reconciled(self):
        TransactionFactory(
            account=self.account,
            reconciled=True,
            amount=10,
            date=datetime.date(2015, 10, 27),
        )
        TransactionFactory(
            account=self.account,
            reconciled=True,
            amount=15,
            date=datetime.date(2015, 10, 28),
        )
        TransactionFactory(
            account=self.account,
            reconciled=False,
            amount=30,
            date=datetime.date(2015, 10, 29),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(response.data['results'][0]['balance_reconciled'], '25.00')
        self.assertEqual(response.data['results'][1]['balance_reconciled'], '25.00')
        self.assertEqual(response.data['results'][2]['balance_reconciled'], '10.00')


class PartialUpdateMultipleViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.account = AccountFactory(currency='EUR')
        cls.url = reverse('transaction-partial-update-multiple')

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 401)

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
        bt = TransactionFactory(account=self.account)
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [-1, bt.pk],
        })
        self.assertEqual(response.status_code, 400)

    def test_invalid_reconciled(self):
        bt = TransactionFactory(account=self.account)
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
            'reconciled': 'foo'
        })
        self.assertEqual(response.status_code, 400)

    def test_invalid_status(self):
        bt = TransactionFactory(account=self.account)
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
            'status': 'foo'
        })
        self.assertEqual(response.status_code, 400)

    def test_update_multiple_no_field(self):
        bt = TransactionFactory(account=self.account)

        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
        })
        self.assertEqual(response.status_code, 200)

    def test_update_multiple_field_not_allowed(self):
        bt = TransactionFactory(account=self.account, amount=20)

        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
            'amount': 10,
        })
        self.assertEqual(response.status_code, 200)
        bt.refresh_from_db()
        self.assertEqual(bt.amount, Decimal('20'))

    def test_update_multiple_reconciled_boolean(self):
        bt1 = TransactionFactory(account=self.account, reconciled=True)
        bt2 = TransactionFactory(account=self.account, reconciled=False)

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
        bt = TransactionFactory(account=self.account, reconciled=False)
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
            'reconciled': 1,
        })
        self.assertEqual(response.status_code, 200)
        bt.refresh_from_db()
        self.assertTrue(bt.reconciled)

    def test_update_multiple_reconciled_string(self):
        bt = TransactionFactory(account=self.account, reconciled=False)
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
            'reconciled': 'true',
        })
        self.assertEqual(response.status_code, 200)
        bt.refresh_from_db()
        self.assertTrue(bt.reconciled)

    def test_update_multiple_unreconciled_boolean(self):
        bt1 = TransactionFactory(account=self.account, reconciled=True)
        bt2 = TransactionFactory(account=self.account, reconciled=False)

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
        bt = TransactionFactory(account=self.account, reconciled=True)
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
            'reconciled': 0,
        })
        self.assertEqual(response.status_code, 200)
        bt.refresh_from_db()
        self.assertFalse(bt.reconciled)

    def test_update_multiple_unreconciled_string(self):
        bt = TransactionFactory(account=self.account, reconciled=True)
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, data={
            'ids': [bt.pk],
            'reconciled': "false",
        })
        self.assertEqual(response.status_code, 200)
        bt.refresh_from_db()
        self.assertFalse(bt.reconciled)

    def test_update_multiple_status(self):
        bt1 = TransactionFactory(
            account=self.account,
            status=Transaction.STATUS_INACTIVE,
        )
        bt2 = TransactionFactory(
            account=self.account,
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
        cls.user = UserFactory()
        cls.account = AccountFactory(currency='EUR')
        cls.url = reverse('transaction-delete-multiple')

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 401)

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
        bt = TransactionFactory(account=self.account)
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url, data={
            'ids': [-1, bt.pk],
        })
        self.assertEqual(response.status_code, 400)

    def test_delete_multiple(self):
        bt1 = TransactionFactory(account=self.account)
        bt2 = TransactionFactory(account=self.account)

        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url, data={
            'ids': [bt1.pk, bt2.pk],
        })
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(Transaction.DoesNotExist):
            bt1.refresh_from_db()
        with self.assertRaises(Transaction.DoesNotExist):
            bt2.refresh_from_db()
