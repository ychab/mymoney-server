import datetime
from decimal import Decimal
from unittest import mock

from django.utils import timezone

from rest_framework.pagination import PageNumberPagination
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from mymoney.accounts.factories import AccountFactory
from mymoney.core.factories import UserFactory
from mymoney.tags.factories import TagFactory
from mymoney.transactions.factories import TransactionFactory
from mymoney.transactions.models import Transaction

from ..factories import SchedulerFactory
from ..models import Scheduler


class CreateViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.account = AccountFactory(currency='USD')
        cls.url = reverse('scheduler-list')

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
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.account, self.account)

    def test_date_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.date, datetime.date.today())

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
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertNotEqual(scheduler.currency, 'EUR')
        self.assertEqual(scheduler.currency, self.account.currency)

    def test_status_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.status, Scheduler.STATUS_ACTIVE)

    def test_reconciled_not_editable(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
            'reconciled': True,
        })
        self.assertEqual(response.status_code, 201)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertFalse(scheduler.reconciled)

    def test_payment_method_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(
            scheduler.payment_method,
            Scheduler.PAYMENT_METHOD_CREDIT_CARD,
        )

    def test_memo_blank(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.memo, '')

    def test_tag_none(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertIsNone(scheduler.tag)

    def test_tag(self):
        tag = TagFactory()

        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': -10,
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 201)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.tag, tag)

    def test_type_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(
            scheduler.type,
            Scheduler.TYPE_MONTHLY,
        )

    def test_recurrence_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertIsNone(scheduler.recurrence)

    def test_last_action_not_editable(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
            'last_action': timezone.now(),
        })
        self.assertEqual(response.status_code, 201)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertIsNone(scheduler.last_action)

    def test_state_not_editable(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
            'state': Scheduler.STATE_FINISHED,
        })
        self.assertEqual(response.status_code, 201)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(
            scheduler.state,
            Scheduler.STATE_WAITING,
        )

    def test_create(self):
        tag = TagFactory()

        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': -10,
            'date': datetime.date(2015, 10, 26),
            'status': Scheduler.STATUS_IGNORED,
            'payment_method': Scheduler.PAYMENT_METHOD_CASH,
            'memo': 'blah blah blah',
            'tag': tag.pk,
            'type': Scheduler.TYPE_WEEKLY,
            'recurrence': 3,
        })
        self.assertEqual(response.status_code, 201)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.label, 'foo')
        self.assertEqual(scheduler.amount, Decimal(-10))
        self.assertEqual(scheduler.date, datetime.date(2015, 10, 26))
        self.assertEqual(scheduler.status, Scheduler.STATUS_IGNORED)
        self.assertFalse(scheduler.reconciled)
        self.assertEqual(scheduler.payment_method, Scheduler.PAYMENT_METHOD_CASH)
        self.assertEqual(scheduler.memo, 'blah blah blah')
        self.assertEqual(scheduler.tag, tag)
        self.assertEqual(scheduler.type, Scheduler.TYPE_WEEKLY)
        self.assertEqual(scheduler.recurrence, 3)

    def test_create_now(self):
        Transaction.objects.all().delete()
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': -10,
            'start_now': True,
        })
        self.assertEqual(response.status_code, 201)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.label, 'foo')
        bt = Transaction.objects.first()
        self.assertEqual(bt.label, 'foo')


class RetrieveViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.account = AccountFactory(currency='USD')
        cls.scheduler = SchedulerFactory(account=cls.account)
        cls.url = reverse('scheduler-detail', kwargs={
            'pk': cls.scheduler.pk,
        })

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class PartialUpdateViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.account = AccountFactory(currency='EUR')
        cls.scheduler = SchedulerFactory(account=cls.account)
        cls.url = reverse('scheduler-detail', kwargs={
            'pk': cls.scheduler.pk,
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
        scheduler = SchedulerFactory(
            account=self.account,
            label='foo',
        )
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'label': 'bar'
        })
        self.assertEqual(response.status_code, 200)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.label, 'bar')

    def test_account_not_editable(self):
        scheduler = SchedulerFactory(account=self.account)
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'account': AccountFactory().pk,
        })
        self.assertEqual(response.status_code, 200)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.account, self.account)

    def test_update_date(self):
        scheduler = SchedulerFactory(
            account=self.account,
            date=datetime.date(2015, 10, 27),
        )
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'date': datetime.date(2015, 10, 10),
        })
        self.assertEqual(response.status_code, 200)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.date, datetime.date(2015, 10, 10))

    def test_update_status(self):
        scheduler = SchedulerFactory(
            account=self.account,
            status=Scheduler.STATUS_ACTIVE,
        )
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'status': Scheduler.STATUS_INACTIVE,
        })
        self.assertEqual(response.status_code, 200)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.status, Scheduler.STATUS_INACTIVE)

    def test_currency_not_editable(self):
        scheduler = SchedulerFactory(account=self.account)
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={'currency': 'USD'})
        self.assertEqual(response.status_code, 200)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.currency, self.account.currency)

    def test_update_amount(self):
        scheduler = SchedulerFactory(
            account=self.account,
            amount='10',
        )
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'amount': '20',
        })
        self.assertEqual(response.status_code, 200)

        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.amount, Decimal('20'))

    def test_update_reconciled_not_editable(self):
        scheduler = SchedulerFactory(
            account=self.account,
            reconciled=False,
        )
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'reconciled': True,
        })
        self.assertEqual(response.status_code, 200)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertFalse(scheduler.reconciled)

    def test_update_payment_method(self):
        scheduler = SchedulerFactory(
            account=self.account,
            payment_method=Scheduler.PAYMENT_METHOD_CASH,
        )
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'payment_method': Scheduler.PAYMENT_METHOD_CHECK,
        })
        self.assertEqual(response.status_code, 200)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.payment_method, Scheduler.PAYMENT_METHOD_CHECK)

    def test_update_memo(self):
        scheduler = SchedulerFactory(
            account=self.account,
            memo='',
        )
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'memo': 'blah blah',
        })
        self.assertEqual(response.status_code, 200)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.memo, 'blah blah')

    def test_add_tag(self):
        tag = TagFactory()
        scheduler = SchedulerFactory(account=self.account)
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.tag, tag)

    def test_update_tag(self):
        tag = TagFactory()
        scheduler = SchedulerFactory(
            account=self.account,
            tag=TagFactory(),
        )
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.tag, tag)

    def test_remove_tag(self):
        scheduler = SchedulerFactory(
            account=self.account,
            tag=TagFactory(),
        )
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'tag': None,
        })
        self.assertEqual(response.status_code, 200)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertIsNone(scheduler.tag)

    def test_update_type(self):
        scheduler = SchedulerFactory(
            account=self.account,
            type=Scheduler.TYPE_MONTHLY,
        )
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'type': Scheduler.TYPE_WEEKLY,
        })
        self.assertEqual(response.status_code, 200)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.type, Scheduler.TYPE_WEEKLY)

    def test_update_recurrence(self):
        scheduler = SchedulerFactory(
            account=self.account,
            recurrence=4,
        )
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'recurrence': None,
        })
        self.assertEqual(response.status_code, 200)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertIsNone(scheduler.recurrence)

    def test_update_last_action_not_editable(self):
        scheduler = SchedulerFactory(
            account=self.account,
            state=Scheduler.STATE_FINISHED,
            last_action=timezone.make_aware(datetime.datetime(2015, 11, 1)),
        )
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'last_action': timezone.make_aware(datetime.datetime(2015, 11, 15)),
        })
        self.assertEqual(response.status_code, 200)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(
            scheduler.last_action,
            timezone.make_aware(datetime.datetime(2015, 11, 1)),
        )

    def test_update_state_not_editable(self):
        scheduler = SchedulerFactory(
            account=self.account,
            state=Scheduler.STATE_WAITING,
        )
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'state': Scheduler.STATE_FAILED,
        })
        self.assertEqual(response.status_code, 200)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.state, Scheduler.STATE_WAITING)

    def test_partial_update(self):
        tag = TagFactory()
        scheduler = SchedulerFactory(
            account=self.account,
            label='foo',
            date=datetime.date(2015, 10, 27),
            amount=0,
            status=Scheduler.STATUS_INACTIVE,
            reconciled=False,
            payment_method=Scheduler.PAYMENT_METHOD_CREDIT_CARD,
            memo='',
            type=Scheduler.TYPE_MONTHLY,
            recurrence=None,
        )
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'label': 'bar',
            'date': datetime.date(2015, 10, 10),
            'amount': 10,
            'status': Scheduler.STATUS_ACTIVE,
            'payment_method': Scheduler.PAYMENT_METHOD_CASH,
            'memo': 'blah blah',
            'tag': tag.pk,
            'type': Scheduler.TYPE_WEEKLY,
            'recurrence': 3,
        })
        self.assertEqual(response.status_code, 200)
        scheduler = Scheduler.objects.get(pk=response.data['id'])
        self.assertEqual(scheduler.label, 'bar')
        self.assertEqual(scheduler.date, datetime.date(2015, 10, 10))
        self.assertEqual(scheduler.amount, Decimal('10'))
        self.assertEqual(scheduler.status, Scheduler.STATUS_ACTIVE)
        self.assertFalse(scheduler.reconciled)
        self.assertEqual(scheduler.payment_method, Scheduler.PAYMENT_METHOD_CASH)
        self.assertEqual(scheduler.memo, 'blah blah')
        self.assertEqual(scheduler.tag, tag)
        self.assertEqual(scheduler.type, Scheduler.TYPE_WEEKLY)
        self.assertEqual(scheduler.recurrence, 3)


class DeleteViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.account = AccountFactory()
        cls.scheduler = SchedulerFactory(account=cls.account)
        cls.url = reverse('scheduler-detail', kwargs={
            'pk': cls.scheduler.pk,
        })

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 401)

    def test_delete(self):
        scheduler = SchedulerFactory(account=self.account)
        url = reverse('scheduler-detail', kwargs={
            'pk': scheduler.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(Scheduler.DoesNotExist):
            scheduler.refresh_from_db()


class ListViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.account = AccountFactory()
        cls.url = reverse('scheduler-list')

    def tearDown(self):
        Scheduler.objects.all().delete()

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
            SchedulerFactory(account=self.account)

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

    def test_other_account(self):
        scheduler = SchedulerFactory(account=self.account)
        SchedulerFactory()
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], scheduler.pk)

    def test_ordering_default(self):
        bts1 = SchedulerFactory(
            account=self.account,
            last_action=None,
        )
        bts2 = SchedulerFactory(
            account=self.account,
            last_action=timezone.make_aware(datetime.datetime(2015, 10, 28)),
        )
        bts3 = SchedulerFactory(
            account=self.account,
            last_action=timezone.make_aware(datetime.datetime(2015, 10, 27)),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertListEqual(
            [bts1.pk, bts2.pk, bts3.pk],
            [scheduler['id'] for scheduler in response.data['results']],
        )


class SummaryViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.account = AccountFactory()
        cls.url = reverse('scheduler-summary')

    def tearDown(self):
        Scheduler.objects.all().delete()

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_none(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)
        self.assertDictEqual(response.data['summary'], {})

    def test_no_credit(self):
        SchedulerFactory(
            account=self.account,
            amount=-10,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=-10,
            type=Scheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['credit'], 0)
        self.assertEqual(response.data['summary']['weekly']['credit'], 0)

    def test_no_debit(self):
        SchedulerFactory(
            account=self.account,
            amount=10,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=10,
            type=Scheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['debit'], 0)
        self.assertEqual(response.data['summary']['weekly']['debit'], 0)

    def test_other_account(self):
        SchedulerFactory(
            account=self.account,
            amount=-10,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(amount=-10)
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_no_monthly(self):
        SchedulerFactory(
            account=self.account,
            amount=-10,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=10,
            type=Scheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('monthly', response.data['summary'])

    def test_no_weekly(self):
        SchedulerFactory(
            account=self.account,
            amount=-10,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=10,
            type=Scheduler.TYPE_MONTHLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('weekly', response.data['summary'])

    def test_monthly_debit(self):
        SchedulerFactory(
            account=self.account,
            amount=-10,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=-5,
            type=Scheduler.TYPE_MONTHLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['debit'], -15)

    def test_monthly_credit(self):
        SchedulerFactory(
            account=self.account,
            amount=10,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=5,
            type=Scheduler.TYPE_MONTHLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['credit'], 15)

    def test_monthly_credit_and_debit(self):
        SchedulerFactory(
            account=self.account,
            amount=10,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=-5,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=-15,
            type=Scheduler.TYPE_MONTHLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['credit'], 10)
        self.assertEqual(response.data['summary']['monthly']['debit'], -20)
        self.assertEqual(response.data['summary']['monthly']['total'], -10)

    def test_weekly_debit(self):
        SchedulerFactory(
            account=self.account,
            amount=-10,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=-5,
            type=Scheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['weekly']['debit'], -15)

    def test_weekly_credit(self):
        SchedulerFactory(
            account=self.account,
            amount=10,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=5,
            type=Scheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['weekly']['credit'], 15)

    def test_weekly_credit_and_debit(self):
        SchedulerFactory(
            account=self.account,
            amount=10,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=-5,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=-15,
            type=Scheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['weekly']['credit'], 10)
        self.assertEqual(response.data['summary']['weekly']['debit'], -20)
        self.assertEqual(response.data['summary']['weekly']['total'], -10)

    def test_credit_and_debit(self):
        SchedulerFactory(
            account=self.account,
            amount=10,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=-5,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=10,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=-5,
            type=Scheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['credit'], 10)
        self.assertEqual(response.data['summary']['monthly']['debit'], -5)
        self.assertEqual(response.data['summary']['monthly']['total'], 5)
        self.assertEqual(response.data['summary']['weekly']['credit'], 10)
        self.assertEqual(response.data['summary']['weekly']['debit'], -5)
        self.assertEqual(response.data['summary']['weekly']['total'], 5)

    def test_total_monthly(self):
        SchedulerFactory(
            account=self.account,
            amount=-10,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=10,
            type=Scheduler.TYPE_MONTHLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)

    def test_total_weekly(self):
        SchedulerFactory(
            account=self.account,
            amount=-10,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=10,
            type=Scheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)

    def test_total_credit(self):
        SchedulerFactory(
            account=self.account,
            amount=10,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=10,
            type=Scheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 20)

    def test_total_debit(self):
        SchedulerFactory(
            account=self.account,
            amount=-10,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=-10,
            type=Scheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], -20)

    def test_total_all(self):
        SchedulerFactory(
            account=self.account,
            amount=10,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=-20,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=30,
            type=Scheduler.TYPE_WEEKLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=-40,
            type=Scheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], -20)

    @mock.patch('mymoney.transactions.models.timezone.now')
    def test_used_nothing(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.datetime(2015, 11, 2))

        SchedulerFactory(
            account=self.account,
            amount=1000,
            type=Scheduler.TYPE_MONTHLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['used'], 0)

    @mock.patch('mymoney.transactions.models.timezone.now')
    def test_used_some_credit(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.datetime(2015, 11, 20))

        SchedulerFactory(
            account=self.account,
            amount=1000,
            type=Scheduler.TYPE_MONTHLY,
        )
        TransactionFactory(
            account=self.account,
            amount=-500,
            date=datetime.date(2015, 11, 15),
            scheduled=False,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['used'], -500)
        self.assertEqual(response.data['summary']['monthly']['remaining'], 500)

    @mock.patch('mymoney.transactions.models.timezone.now')
    def test_used_some_credit_and_debit(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.datetime(2015, 11, 20))

        SchedulerFactory(
            account=self.account,
            amount=1000,
            type=Scheduler.TYPE_MONTHLY,
        )
        SchedulerFactory(
            account=self.account,
            amount=-300,
            type=Scheduler.TYPE_MONTHLY,
        )
        TransactionFactory(
            account=self.account,
            amount=-500,
            date=datetime.date(2015, 11, 15),
            scheduled=False,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['used'], -500)
        self.assertEqual(response.data['summary']['monthly']['remaining'], 200)
