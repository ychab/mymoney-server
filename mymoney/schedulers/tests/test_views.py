import datetime
from decimal import Decimal
from unittest import mock

from django.utils import timezone

from rest_framework.pagination import PageNumberPagination
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from mymoney.bankaccounts import BankAccountFactory
from mymoney.banktransactions.factories import BankTransactionFactory
from mymoney.banktransactions import BankTransaction
from mymoney.banktransactiontags import BankTransactionTagFactory
from mymoney.api.users.factories import UserFactory

from ..factories import BankTransactionSchedulerFactory
from ..models import BankTransactionScheduler


class CreateViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(user_permissions='all')
        cls.bankaccount = BankAccountFactory(currency='USD', owners=[cls.user])
        cls.url = reverse(
            'banktransactionschedulers:banktransactionscheduler-list', kwargs={
                'bankaccount_pk': cls.bankaccount.pk,
            }
        )

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
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.bankaccount, self.bankaccount)

    def test_date_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.date, datetime.date.today())

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
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertNotEqual(bts.currency, 'EUR')
        self.assertEqual(bts.currency, self.bankaccount.currency)

    def test_status_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.status, BankTransactionScheduler.STATUS_ACTIVE)

    def test_reconciled_not_editable(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
            'reconciled': True,
        })
        self.assertEqual(response.status_code, 201)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertFalse(bts.reconciled)

    def test_payment_method_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(
            bts.payment_method,
            BankTransactionScheduler.PAYMENT_METHOD_CREDIT_CARD,
        )

    def test_memo_blank(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.memo, '')

    def test_tag_none(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertIsNone(bts.tag)

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
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.tag, tag)

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
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.tag, tag)

    def test_type_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(
            bts.type,
            BankTransactionScheduler.TYPE_MONTHLY,
        )

    def test_recurrence_default(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
        })
        self.assertEqual(response.status_code, 201)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertIsNone(bts.recurrence)

    def test_last_action_not_editable(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
            'last_action': timezone.now(),
        })
        self.assertEqual(response.status_code, 201)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertIsNone(bts.last_action)

    def test_state_not_editable(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': 10,
            'state': BankTransactionScheduler.STATE_FINISHED,
        })
        self.assertEqual(response.status_code, 201)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(
            bts.state,
            BankTransactionScheduler.STATE_WAITING,
        )

    def test_create(self):
        tag = BankTransactionTagFactory(owner=self.user)

        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': -10,
            'date': datetime.date(2015, 10, 26),
            'status': BankTransactionScheduler.STATUS_IGNORED,
            'payment_method': BankTransactionScheduler.PAYMENT_METHOD_CASH,
            'memo': 'blah blah blah',
            'tag': tag.pk,
            'type': BankTransactionScheduler.TYPE_WEEKLY,
            'recurrence': 3,
        })
        self.assertEqual(response.status_code, 201)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.label, 'foo')
        self.assertEqual(bts.amount, Decimal(-10))
        self.assertEqual(bts.date, datetime.date(2015, 10, 26))
        self.assertEqual(bts.status, BankTransactionScheduler.STATUS_IGNORED)
        self.assertFalse(bts.reconciled)
        self.assertEqual(bts.payment_method, BankTransactionScheduler.PAYMENT_METHOD_CASH)
        self.assertEqual(bts.memo, 'blah blah blah')
        self.assertEqual(bts.tag, tag)
        self.assertEqual(bts.type, BankTransactionScheduler.TYPE_WEEKLY)
        self.assertEqual(bts.recurrence, 3)

    def test_create_now(self):
        BankTransaction.objects.all().delete()
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={
            'label': 'foo',
            'amount': -10,
            'start_now': True,
        })
        self.assertEqual(response.status_code, 201)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.label, 'foo')
        bt = BankTransaction.objects.first()
        self.assertEqual(bt.label, 'foo')


class PartialUpdateViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(user_permissions='all')
        cls.bankaccount = BankAccountFactory(currency='EUR', owners=[cls.user])
        cls.bts = BankTransactionSchedulerFactory(bankaccount=cls.bankaccount)
        cls.url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': cls.bts.pk,
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
        bts = BankTransactionSchedulerFactory()
        self.client.force_authenticate(user)
        response = self.client.patch(
            reverse('banktransactionschedulers:banktransactionscheduler-detail',
                    kwargs={'pk': bts.pk})
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
        bts = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            label='foo',
        )
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'label': 'bar'
        })
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.label, 'bar')

    def test_bankaccount_not_editable(self):
        bts = BankTransactionSchedulerFactory(bankaccount=self.bankaccount)
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'bankaccount': BankAccountFactory().pk,
        })
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.bankaccount, self.bankaccount)

    def test_update_date(self):
        bts = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 27),
        )
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'date': datetime.date(2015, 10, 10),
        })
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.date, datetime.date(2015, 10, 10))

    def test_update_status(self):
        bts = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            status=BankTransactionScheduler.STATUS_ACTIVE,
        )
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'status': BankTransactionScheduler.STATUS_INACTIVE,
        })
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.status, BankTransactionScheduler.STATUS_INACTIVE)

    def test_currency_not_editable(self):
        bts = BankTransactionSchedulerFactory(bankaccount=self.bankaccount)
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={'currency': 'USD'})
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.currency, self.bankaccount.currency)

    def test_update_amount(self):
        bts = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount='10',
        )
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'amount': '20',
        })
        self.assertEqual(response.status_code, 200)

        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.amount, Decimal('20'))

    def test_update_reconciled_not_editable(self):
        bts = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            reconciled=False,
        )
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'reconciled': True,
        })
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertFalse(bts.reconciled)

    def test_update_payment_method(self):
        bts = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            payment_method=BankTransactionScheduler.PAYMENT_METHOD_CASH,
        )
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'payment_method': BankTransactionScheduler.PAYMENT_METHOD_CHECK,
        })
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.payment_method, BankTransactionScheduler.PAYMENT_METHOD_CHECK)

    def test_update_memo(self):
        bts = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            memo='',
        )
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'memo': 'blah blah',
        })
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.memo, 'blah blah')

    def test_add_tag(self):
        tag = BankTransactionTagFactory(owner=self.user)
        bts = BankTransactionSchedulerFactory(bankaccount=self.bankaccount)
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.tag, tag)

    def test_update_tag(self):
        tag = BankTransactionTagFactory(owner=self.user)
        bts = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            tag=BankTransactionTagFactory(owner=self.user),
        )
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.tag, tag)

    def test_remove_tag(self):
        bts = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            tag=BankTransactionTagFactory(owner=self.user),
        )
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'tag': None,
        })
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertIsNone(bts.tag)

    def test_update_not_owner_tag(self):
        tag = BankTransactionTagFactory(owner=self.user)
        tag_not_owner = BankTransactionTagFactory()
        bts = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            tag=tag,
        )
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'tag': tag_not_owner.pk,
        })
        self.assertEqual(response.status_code, 400)

    def test_update_type(self):
        bts = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'type': BankTransactionScheduler.TYPE_WEEKLY,
        })
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.type, BankTransactionScheduler.TYPE_WEEKLY)

    def test_update_recurrence(self):
        bts = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            recurrence=4,
        )
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'recurrence': None,
        })
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertIsNone(bts.recurrence)

    def test_update_last_action_not_editable(self):
        bts = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            state=BankTransactionScheduler.STATE_FINISHED,
            last_action=timezone.make_aware(datetime.datetime(2015, 11, 1)),
        )
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'last_action': timezone.make_aware(datetime.datetime(2015, 11, 15)),
        })
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(
            bts.last_action,
            timezone.make_aware(datetime.datetime(2015, 11, 1)),
        )

    def test_update_state_not_editable(self):
        bts = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            state=BankTransactionScheduler.STATE_WAITING,
        )
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'state': BankTransactionScheduler.STATE_FAILED,
        })
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.state, BankTransactionScheduler.STATE_WAITING)

    def test_partial_update(self):
        tag = BankTransactionTagFactory(owner=self.user)
        bts = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            label='foo',
            date=datetime.date(2015, 10, 27),
            amount=0,
            status=BankTransactionScheduler.STATUS_INACTIVE,
            reconciled=False,
            payment_method=BankTransactionScheduler.PAYMENT_METHOD_CREDIT_CARD,
            memo='',
            type=BankTransactionScheduler.TYPE_MONTHLY,
            recurrence=None,
        )
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data={
            'label': 'bar',
            'date': datetime.date(2015, 10, 10),
            'amount': 10,
            'status': BankTransactionScheduler.STATUS_ACTIVE,
            'payment_method': BankTransactionScheduler.PAYMENT_METHOD_CASH,
            'memo': 'blah blah',
            'tag': tag.pk,
            'type': BankTransactionScheduler.TYPE_WEEKLY,
            'recurrence': 3,
        })
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.label, 'bar')
        self.assertEqual(bts.date, datetime.date(2015, 10, 10))
        self.assertEqual(bts.amount, Decimal('10'))
        self.assertEqual(bts.status, BankTransactionScheduler.STATUS_ACTIVE)
        self.assertFalse(bts.reconciled)
        self.assertEqual(bts.payment_method, BankTransactionScheduler.PAYMENT_METHOD_CASH)
        self.assertEqual(bts.memo, 'blah blah')
        self.assertEqual(bts.tag, tag)
        self.assertEqual(bts.type, BankTransactionScheduler.TYPE_WEEKLY)
        self.assertEqual(bts.recurrence, 3)


class UpdateViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(user_permissions='all')
        cls.bankaccount = BankAccountFactory(owners=[cls.user])
        cls.bts = BankTransactionSchedulerFactory(bankaccount=cls.bankaccount)
        cls.url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': cls.bts.pk,
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
        bts = BankTransactionSchedulerFactory()
        self.client.force_authenticate(user)
        response = self.client.put(
            reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
                'pk': bts.pk})
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
        bts = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            label='foo',
            date=datetime.date(2015, 10, 27),
            amount=0,
            status=BankTransactionScheduler.STATUS_INACTIVE,
            reconciled=False,
            payment_method=BankTransactionScheduler.PAYMENT_METHOD_CREDIT_CARD,
            memo='',
            tag=BankTransactionTagFactory(owner=self.user),
            type=BankTransactionScheduler.TYPE_MONTHLY,
            recurrence=2,
        )
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.put(url, data={
            'label': 'bar',
            'date': datetime.date(2015, 10, 10),
            'amount': 10,
            'status': BankTransactionScheduler.STATUS_ACTIVE,
            'payment_method': BankTransactionScheduler.PAYMENT_METHOD_CASH,
            'memo': 'blah blah',
            'tag': tag.pk,
            'type': BankTransactionScheduler.TYPE_WEEKLY,
            'recurrence': 4,
        })
        self.assertEqual(response.status_code, 200)
        bts = BankTransactionScheduler.objects.get(pk=response.data['id'])
        self.assertEqual(bts.label, 'bar')
        self.assertEqual(bts.date, datetime.date(2015, 10, 10))
        self.assertEqual(bts.amount, Decimal('10'))
        self.assertEqual(bts.status, BankTransactionScheduler.STATUS_ACTIVE)
        self.assertFalse(bts.reconciled)
        self.assertEqual(bts.payment_method, BankTransactionScheduler.PAYMENT_METHOD_CASH)
        self.assertEqual(bts.memo, 'blah blah')
        self.assertEqual(bts.tag, tag)
        self.assertEqual(bts.type, BankTransactionScheduler.TYPE_WEEKLY)
        self.assertEqual(bts.recurrence, 4)


class DeleteViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(user_permissions='all')
        cls.bankaccount = BankAccountFactory(owners=[cls.user])
        cls.bts = BankTransactionSchedulerFactory(bankaccount=cls.bankaccount)
        cls.url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': cls.bts.pk,
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
        bts = BankTransactionSchedulerFactory()
        self.client.force_authenticate(user)
        response = self.client.delete(
            reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
                'pk': bts.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_access_not_owner_with_permissions(self):
        user = UserFactory(user_permissions='all')
        self.client.force_authenticate(user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_granted(self):
        bts = BankTransactionSchedulerFactory(bankaccount=self.bankaccount)
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_delete(self):
        bts = BankTransactionSchedulerFactory(bankaccount=self.bankaccount)
        url = reverse('banktransactionschedulers:banktransactionscheduler-detail', kwargs={
            'pk': bts.pk,
        })
        self.client.force_authenticate(self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(BankTransactionScheduler.DoesNotExist):
            bts.refresh_from_db()


class ListViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.bankaccount = BankAccountFactory(owners=[cls.user])
        cls.url = reverse('banktransactionschedulers:banktransactionscheduler-list', kwargs={
            'bankaccount_pk': cls.bankaccount.pk,
        })

    def tearDown(self):
        BankTransactionScheduler.objects.all().delete()

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
            BankTransactionSchedulerFactory(bankaccount=self.bankaccount)

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
        bts = BankTransactionSchedulerFactory(bankaccount=self.bankaccount)
        BankTransactionSchedulerFactory()
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], bts.pk)

    def test_ordering_default(self):
        bts1 = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            last_action=None,
        )
        bts2 = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            last_action=timezone.make_aware(datetime.datetime(2015, 10, 28)),
        )
        bts3 = BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            last_action=timezone.make_aware(datetime.datetime(2015, 10, 27)),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertListEqual(
            [bts1.pk, bts2.pk, bts3.pk],
            [bts['id'] for bts in response.data['results']],
        )


class SummaryViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.bankaccount = BankAccountFactory(owners=[cls.user])
        cls.url = reverse('banktransactionschedulers:banktransactionscheduler-summary', kwargs={
            'bankaccount_pk': cls.bankaccount.pk,
        })

    def tearDown(self):
        BankTransactionScheduler.objects.all().delete()

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

    def test_none(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)
        self.assertDictEqual(response.data['summary'], {})

    def test_no_credit(self):
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-10,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['credit'], 0)
        self.assertEqual(response.data['summary']['weekly']['credit'], 0)

    def test_no_debit(self):
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=10,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['debit'], 0)
        self.assertEqual(response.data['summary']['weekly']['debit'], 0)

    def test_other_bankaccount(self):
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(amount=-10)
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_no_monthly(self):
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-10,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=10,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('monthly', response.data['summary'])

    def test_no_weekly(self):
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('weekly', response.data['summary'])

    def test_monthly_debit(self):
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-5,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['debit'], -15)

    def test_monthly_credit(self):
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=5,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['credit'], 15)

    def test_monthly_credit_and_debit(self):
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-5,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-15,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['credit'], 10)
        self.assertEqual(response.data['summary']['monthly']['debit'], -20)
        self.assertEqual(response.data['summary']['monthly']['total'], -10)

    def test_weekly_debit(self):
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-10,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-5,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['weekly']['debit'], -15)

    def test_weekly_credit(self):
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=10,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=5,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['weekly']['credit'], 15)

    def test_weekly_credit_and_debit(self):
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=10,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-5,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-15,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['weekly']['credit'], 10)
        self.assertEqual(response.data['summary']['weekly']['debit'], -20)
        self.assertEqual(response.data['summary']['weekly']['total'], -10)

    def test_credit_and_debit(self):
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-5,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=10,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-5,
            type=BankTransactionScheduler.TYPE_WEEKLY,
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
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)

    def test_total_weekly(self):
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-10,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=10,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)

    def test_total_credit(self):
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=10,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 20)

    def test_total_debit(self):
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-10,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], -20)

    def test_total_all(self):
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=10,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-20,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=30,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-40,
            type=BankTransactionScheduler.TYPE_WEEKLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], -20)

    @mock.patch('mymoney.api.banktransactions.models.timezone.now')
    def test_used_nothing(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.datetime(2015, 11, 2))

        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=1000,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['used'], 0)

    @mock.patch('mymoney.api.banktransactions.models.timezone.now')
    def test_used_some_credit(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.datetime(2015, 11, 20))

        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=1000,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            amount=-500,
            date=datetime.date(2015, 11, 15),
            scheduled=False,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['used'], -500)
        self.assertEqual(response.data['summary']['monthly']['remaining'], 500)

    @mock.patch('mymoney.api.banktransactions.models.timezone.now')
    def test_used_some_credit_and_debit(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.datetime(2015, 11, 20))

        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=1000,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionSchedulerFactory(
            bankaccount=self.bankaccount,
            amount=-300,
            type=BankTransactionScheduler.TYPE_MONTHLY,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            amount=-500,
            date=datetime.date(2015, 11, 15),
            scheduled=False,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['monthly']['used'], -500)
        self.assertEqual(response.data['summary']['monthly']['remaining'], 200)
