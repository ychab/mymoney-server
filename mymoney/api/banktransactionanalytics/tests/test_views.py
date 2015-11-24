import datetime

from django.test import override_settings

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from mymoney.api.bankaccounts.factories import BankAccountFactory
from mymoney.api.banktransactions.factories import BankTransactionFactory
from mymoney.api.banktransactions.models import BankTransaction
from mymoney.api.banktransactiontags.factories import BankTransactionTagFactory
from mymoney.api.users.factories import UserFactory
from mymoney.core.utils.dates import GRANULARITY_MONTH, GRANULARITY_WEEK

from ..serializers import RatioInputSerializer


class RatioListViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.bankaccount = BankAccountFactory(owners=[cls.user])
        cls.url = reverse('banktransactionanalytics:ratio-list', kwargs={
            'bankaccount_pk': cls.bankaccount.pk,
        })

    def tearDown(self):
        BankTransaction.objects.all().delete()

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

    def test_date_start_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date_end': datetime.date(2015, 11, 2),
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('date_start', response.data)

    def test_date_end_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date_start': datetime.date(2015, 11, 2),
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('date_end', response.data)

    def test_none(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.data['results'], [])
        self.assertIsNone(response.data['total'])

    def test_amount_none(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=0,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.data['results'], [])
        self.assertIsNone(response.data['total'])

    def test_other_bankaccount(self):
        BankTransactionFactory(date=datetime.date(2015, 11, 2), amount=-10)

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.data['results'], [])

    def test_status_inactive(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            status=BankTransaction.STATUS_INACTIVE,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.data['results'], [])

    def test_single_debit(self):
        tag = BankTransactionTagFactory(owner=self.user)

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=10,
            tag=tag,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SINGLE_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], -20)

    def test_single_credit(self):
        tag = BankTransactionTagFactory(owner=self.user)

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=10,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=10,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=tag,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SINGLE_CREDIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 20)

    def test_reconciled_none(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            reconciled=True,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            reconciled=False,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], -30)

    def test_reconciled(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            reconciled=True,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            reconciled=False,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'reconciled': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], -10)

    def test_unreconciled(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            reconciled=True,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            reconciled=False,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'reconciled': False,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], -20)

    def test_sum_debit(self):
        tag = BankTransactionTagFactory(owner=self.user)

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=10,
            tag=tag,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], -40)

    def test_sum_credit(self):
        tag = BankTransactionTagFactory(owner=self.user)

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=50,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=tag,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_CREDIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 40)

    def test_date_ranges(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
            amount=-10,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 30),
            amount=-10,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 31),
            amount=-30,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], -20)

    def test_tags_none(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
            amount=-10,
            tag=None,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIsNone(response.data['results'][0]['tag'])
        self.assertEqual(response.data['subtotal'], -10)
        self.assertEqual(response.data['total'], -10)

    def test_tags_single(self):
        tag = BankTransactionTagFactory(owner=self.user)

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=None,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tags': [tag.pk],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['tag']['id'], tag.pk)
        self.assertEqual(response.data['results'][0]['tag']['name'], tag.name)
        self.assertEqual(response.data['subtotal'], -50)
        self.assertEqual(response.data['total'], -60)

    def test_tags_multiple(self):
        tag1 = BankTransactionTagFactory(owner=self.user)
        tag2 = BankTransactionTagFactory(owner=self.user)

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=tag1,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=tag2,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=None,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tags': [tag1.pk, tag2.pk],
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            [tag1.pk, tag2.pk],
            sorted([row['tag']['id'] for row in response.data['results']]),
        )
        self.assertEqual(response.data['subtotal'], -60)
        self.assertEqual(response.data['total'], -80)

    def test_sum_min(self):
        tag = BankTransactionTagFactory(owner=self.user)

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-40,
            tag=None,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'sum_min': -35,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['tag']['id'], tag.pk)
        self.assertEqual(response.data['subtotal'], -30)
        self.assertEqual(response.data['total'], -70)

    def test_sum_max(self):
        tag = BankTransactionTagFactory(owner=self.user)

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-40,
            tag=None,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'sum_max': -45,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['tag']['id'], tag.pk)
        self.assertEqual(response.data['subtotal'], -50)
        self.assertEqual(response.data['total'], -90)

    def test_sum_ranges(self):
        tag = BankTransactionTagFactory(owner=self.user)

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-80,
            tag=BankTransactionTagFactory(),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=None,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'sum_min': -60,
            'sum_max': -40,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['tag']['id'], tag.pk)
        self.assertEqual(response.data['subtotal'], -50)
        self.assertEqual(response.data['total'], -160)

    def test_group_by_tag_only_one(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=None,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['sum'], '-10.00')
        self.assertEqual(response.data['results'][0]['count'], 1)
        self.assertEqual(response.data['total'], -10)

    def test_group_by_tag_more(self):
        tag = BankTransactionTagFactory(owner=self.user)

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=tag,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['sum'], '-50.00')
        self.assertEqual(response.data['results'][0]['count'], 2)
        self.assertEqual(response.data['total'], -50)

    def test_subtotal_is_total(self):
        tag = BankTransactionTagFactory()

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=None,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['subtotal'], -60)
        self.assertEqual(response.data['total'], -60)

    def test_subtotal_by_sum(self):
        tag = BankTransactionTagFactory()

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=BankTransactionTagFactory(),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'sum_max': -40,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['subtotal'], -50)
        self.assertEqual(response.data['total'], -60)

    def test_subtotal_by_tag(self):
        tag = BankTransactionTagFactory(owner=self.user)

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=None,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tags': [tag.pk],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['subtotal'], -50)
        self.assertEqual(response.data['total'], -60)

    def test_total(self):
        tag = BankTransactionTagFactory(owner=self.user)

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=BankTransactionTagFactory(),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=BankTransactionTagFactory(),
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['total'], -60)

    def test_tag_serializer_none(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=None,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIsNone(response.data['results'][0]['tag'])

    def test_tag_serializer(self):
        tag = BankTransactionTagFactory(owner=self.user)
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=tag,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['tag']['id'], tag.pk)
        self.assertEqual(response.data['results'][0]['tag']['name'], tag.name)

    def test_percentage_partial(self):
        tag = BankTransactionTagFactory(owner=self.user)
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=BankTransactionTagFactory(),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=None,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['results'][0]['percentage'], '33.33')
        self.assertEqual(response.data['total'], -150)

    def test_percentage_all(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=None,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['percentage'], '100.00')
        self.assertEqual(response.data['total'], -50)

    def test_count_single(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=BankTransactionTagFactory(),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=None,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['count'], 1)
        self.assertEqual(response.data['results'][1]['count'], 1)

    def test_count_multiple(self):
        tag = BankTransactionTagFactory()

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=tag,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['count'], 2)

    def test_order_debit(self):
        tag1 = BankTransactionTagFactory(owner=self.user)
        tag2 = BankTransactionTagFactory(owner=self.user)

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-150,
            tag=tag1,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=tag2,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-80,
            tag=None,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        self.assertListEqual(
            [tag1.pk, None, tag2.pk],
            [row['tag']['id'] if row['tag'] else None for row in response.data['results']],
        )

    def test_order_credit(self):
        tag1 = BankTransactionTagFactory(owner=self.user)
        tag2 = BankTransactionTagFactory(owner=self.user)

        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=150,
            tag=tag1,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=50,
            tag=tag2,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=80,
            tag=None,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_CREDIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        self.assertListEqual(
            [tag1.pk, None, tag2.pk],
            [row['tag']['id'] if row['tag'] else None for row in response.data['results']],
        )


class RatioSummaryViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.tag = BankTransactionTagFactory(owner=cls.user)
        cls.bankaccount = BankAccountFactory(owners=[cls.user])
        cls.url = reverse('banktransactionanalytics:ratio-summary', kwargs={
            'bankaccount_pk': cls.bankaccount.pk,
        })

    def tearDown(self):
        BankTransaction.objects.all().delete()

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_bankaccount_not_owner(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 403)

    def test_date_start_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date_end': datetime.date(2015, 11, 2),
            'tag': '',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('date_start', response.data)

    def test_date_end_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date_start': datetime.date(2015, 11, 2),
            'tag': '',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('date_end', response.data)

    def test_dates_range(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date_start': datetime.date(2015, 11, 2),
            'date_end': datetime.date(2015, 11, 1),
            'tag': '',
        })
        self.assertEqual(response.status_code, 400)

    def test_tag_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date_start': datetime.date(2015, 11, 2),
            'date_end': datetime.date(2015, 11, 3),
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('tag', response.data)

    def test_tag_not_owner(self):
        tag = BankTransactionTagFactory()
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': tag.pk,
        })
        self.assertEqual(response.status_code, 400)

    def test_tag_unknown(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': -1,
        })
        self.assertEqual(response.status_code, 400)

    def test_none(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.data['results'], [])
        self.assertEqual(response.data['total'], 0)

    def test_other_bankaccount(self):
        BankTransactionFactory(
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=self.tag,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': self.tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.data['results'], [])

    def test_date_ranges(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
            amount=-30,
            tag=self.tag,
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 30),
            amount=-20,
            tag=self.tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 30),
            amount=-10,
            tag=self.tag,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': self.tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            [bt1.pk, bt2.pk],
            sorted([bt['id'] for bt in response.data['results']])
        )

    def test_status_inactive(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            status=BankTransaction.STATUS_INACTIVE,
            tag=self.tag,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': self.tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.data['results'], [])

    def test_single_debit(self):
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=self.tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=20,
            tag=self.tag,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SINGLE_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': self.tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], bt.pk)

    def test_single_credit(self):
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=10,
            tag=self.tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=self.tag,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SINGLE_CREDIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': self.tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], bt.pk)

    def test_reconciled_none(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            reconciled=True,
            tag=self.tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            reconciled=False,
            tag=self.tag,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': self.tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)

    def test_reconciled(self):
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            reconciled=True,
            tag=self.tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            reconciled=False,
            tag=self.tag,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': self.tag.pk,
            'reconciled': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], bt.pk)

    def test_unreconciled(self):
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            reconciled=False,
            tag=self.tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            reconciled=True,
            tag=self.tag,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': self.tag.pk,
            'reconciled': False,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], bt.pk)

    def test_sum_debit(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=self.tag,
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=40,
            tag=self.tag,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': self.tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            [bt1.pk, bt2.pk],
            sorted([bt['id'] for bt in response.data['results']])
        )

    def test_sum_credit(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=50,
            tag=self.tag,
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-40,
            tag=self.tag,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_CREDIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': self.tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            [bt1.pk, bt2.pk],
            sorted([bt['id'] for bt in response.data['results']])
        )

    def test_tag_none(self):
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=None,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-40,
            tag=self.tag,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            [bt.pk],
            sorted([b['id'] for b in response.data['results']])
        )

    def test_tag(self):
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=self.tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-40,
            tag=None,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': self.tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            [bt.pk],
            sorted([b['id'] for b in response.data['results']])
        )

    def test_order_date(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=self.tag,
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 3),
            amount=-50,
            tag=self.tag,
        )
        bt3 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 4),
            amount=-50,
            tag=self.tag,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': self.tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            [bt1.pk, bt2.pk, bt3.pk],
            [bt['id'] for bt in response.data['results']],
        )

    def test_order_date_conflict_id(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=self.tag,
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=self.tag,
        )
        bt3 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=self.tag,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': self.tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            [bt1.pk, bt2.pk, bt3.pk],
            [bt['id'] for bt in response.data['results']],
        )

    def test_total(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=self.tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-40,
            tag=self.tag,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=None,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
            'tag': self.tag.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], -70)


class TrendTimeListViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.bankaccount = BankAccountFactory(owners=[cls.user], balance_initial=0)
        cls.url = reverse('banktransactionanalytics:trendtime-list', kwargs={
            'bankaccount_pk': cls.bankaccount.pk,
        })

    def tearDown(self):
        BankTransaction.objects.all().delete()

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

    def test_date_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('date', response.data)

    def test_none(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 1),
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.data['results'], [])
        self.assertIsNone(response.data['previous'])
        self.assertIsNone(response.data['next'])

    def test_bankaccount_other(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
        )
        BankTransactionFactory(
            date=datetime.date(2015, 11, 10),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_status_inactive(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
            status=BankTransaction.STATUS_ACTIVE,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
            status=BankTransaction.STATUS_INACTIVE,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_reconciled_none(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 11),
            reconciled=True,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 12),
            reconciled=False,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 12),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)

    def test_reconciled(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
            reconciled=True,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            reconciled=False,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 10),
            'reconciled': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_unreconciled(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
            reconciled=False,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            reconciled=True,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 10),
            'reconciled': False,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_granularity_monthly(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 31),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    @override_settings(LANGUAGE_CODE='fr-fr')
    def test_granularity_weekly_fr_fr(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_WEEK,
            'date': datetime.date(2015, 11, 4),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    @override_settings(LANGUAGE_CODE='en-us')
    def test_granularity_weekly_en_us(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 8),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 7),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_WEEK,
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_date_delimiter_out_previous(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 10, 31),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['results'])

    def test_date_delimiter_out_next(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 10),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 1),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['results'])

    def test_date_delimiter_out_other_bankaccount(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 20),
        )
        BankTransactionFactory(
            date=datetime.date(2015, 10, 20),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 10, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['results'])

    def test_date_delimiter_out_inactive(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 20),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 20),
            status=BankTransaction.STATUS_INACTIVE,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 10, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['results'])

    def test_date_delimiter_out_reconciled(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 20),
            reconciled=True,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 20),
            reconciled=False,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 10, 10),
            'reconciled': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['results'])

    def test_date_delimiter_in_previous(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 12, 20),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 3),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 21)  # include 1-20

    def test_date_delimiter_in_next(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 12, 20),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 12, 25),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 20)

    def test_date_ranges_in(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 12, 20),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 30)
        self.assertEqual(response.data['results'][0]['count'], 1)
        self.assertEqual(response.data['results'][1]['count'], 1)
        self.assertEqual(response.data['results'][2]['count'], 0)

    def test_date_ranges_out(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 5),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 12, 20),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            sum([row['count'] for row in response.data['results']], 0),
            0,
        )

    def test_balance_previous_other_bankaccount(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 5),
            amount=-20,
        )
        BankTransactionFactory(
            date=datetime.date(2015, 10, 5),
            amount=-10,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['balance'], '-20.00')

    def test_balance_previous_inactive(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 5),
            amount=-20,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 5),
            amount=-10,
            status=BankTransaction.STATUS_INACTIVE,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['balance'], '-20.00')

    def test_balance_previous_reconciled(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 5),
            amount=-20,
            reconciled=True,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 5),
            amount=-10,
            reconciled=False,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 10),
            'reconciled': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['balance'], '-20.00')

    def test_balance_previous_first(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-10,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['balance'], '-10.00')

    def test_balance_previous(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 20),
            amount=-20,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 31),
            amount=-10,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['balance'], '-10.00')

    def test_balance_initial(self):
        bankaccount = BankAccountFactory(
            owners=[self.user],
            balance_initial=500,
        )
        url = reverse('banktransactionanalytics:trendtime-list', kwargs={
            'bankaccount_pk': bankaccount.pk,
        })

        BankTransactionFactory(
            bankaccount=bankaccount,
            date=datetime.date(2015, 11, 5),
            amount=-20,
        )
        BankTransactionFactory(
            bankaccount=bankaccount,
            date=datetime.date(2015, 10, 5),
            amount=-10,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['balance'], '490.00')

    def test_iterate_ranges(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 10),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 3),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 12, 3),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 30)
        self.assertEqual(response.data['results'][0]['date'], str(datetime.date(2015, 11, 1)))
        self.assertEqual(response.data['results'][3]['date'], str(datetime.date(2015, 11, 4)))

    def test_iterate_first_range(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 3),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 12, 3),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 28)
        self.assertEqual(response.data['results'][0]['date'], str(datetime.date(2015, 11, 3)))

    def test_iterate_last_range(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 3),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 3),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 29),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['results'][0]['date'], str(datetime.date(2015, 11, 1)))
        self.assertEqual(response.data['results'][1]['date'], str(datetime.date(2015, 11, 2)))
        self.assertEqual(response.data['results'][2]['date'], str(datetime.date(2015, 11, 3)))

    def test_date_step_count_none(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 3),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 15),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][1]['count'], 0)

    def test_date_step_count_increment(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 15),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['count'], 2)

    def test_date_step_delta_none(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 3),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 15),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][1]['delta'], '0.00')

    def test_date_step_delta(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
            amount=-10,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
            amount=-20,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 15),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['delta'], '-30.00')

    def test_date_step_balance_none(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
            amount=-10,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 3),
            amount=-20,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 15),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['balance'], '-10.00')
        self.assertEqual(response.data['results'][1]['balance'], '-10.00')

    def test_date_step_balance_increment(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
            amount=-10,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-20,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
            amount=-40,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 15),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['balance'], '-10.00')
        self.assertEqual(response.data['results'][1]['balance'], '-70.00')

    def test_order_date_asc(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 3),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 15),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['date'], str(datetime.date(2015, 11, 1)))
        self.assertEqual(response.data['results'][1]['date'], str(datetime.date(2015, 11, 2)))
        self.assertEqual(response.data['results'][2]['date'], str(datetime.date(2015, 11, 3)))

    def test_pager_previous_none(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 15),
        })
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['previous'])

    def test_pager_previous(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 2),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 15),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['previous'],
            'http://testserver{url}?date=2015-10-01'.format(url=self.url),
        )

    def test_pager_next_none(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 15),
        })
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['next'])

    def test_pager_next(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 2),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 12, 2),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 15),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['next'],
            'http://testserver{url}?date=2015-12-01'.format(url=self.url),
        )

    def test_pager_both_none(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 15),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 15),
        })
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['previous'])
        self.assertIsNone(response.data['next'])

    def test_pager_both(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 15),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 12, 15),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 15),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['previous'],
            'http://testserver{url}?date=2015-10-01'.format(url=self.url),
        )
        self.assertEqual(
            response.data['next'],
            'http://testserver{url}?date=2015-12-01'.format(url=self.url),
        )

    def test_pager_keep_parameters(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 10, 15),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 12, 15),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 15),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['previous'],
            'http://testserver{url}?date=2015-10-01&granularity={granularity}'.format(
                url=self.url,
                granularity=GRANULARITY_MONTH,
            ),
        )
        self.assertEqual(
            response.data['next'],
            'http://testserver{url}?date=2015-12-01&granularity={granularity}'.format(
                url=self.url,
                granularity=GRANULARITY_MONTH,
            ),
        )

    def test_output_serializer(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
            amount=-10,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 1),
            amount=-20,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'granularity': GRANULARITY_MONTH,
            'date': datetime.date(2015, 11, 15),
        })
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            {
                'date': str(datetime.date(2015, 11, 1)),
                'count': 2,
                'balance': '-30.00',
                'delta': '-30.00',
                'percentage': '0.00',
            },
            response.data['results'][0],
        )


class TrendTimeSummaryViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.bankaccount = BankAccountFactory(owners=[cls.user])
        cls.url = reverse('banktransactionanalytics:trendtime-summary', kwargs={
            'bankaccount_pk': cls.bankaccount.pk,
        })

    def tearDown(self):
        BankTransaction.objects.all().delete()

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

    def test_date_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('date', response.data)

    def test_none(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.data['results'], [])

    def test_bankaccount_other(self):
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
        )
        BankTransactionFactory(date=datetime.date(2015, 11, 10))
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            [bt.pk],
            [b['id'] for b in response.data['results']],
        )

    def test_status_inactive(self):
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
            status=BankTransaction.STATUS_ACTIVE,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
            status=BankTransaction.STATUS_INACTIVE,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            [bt.pk],
            [b['id'] for b in response.data['results']],
        )

    def test_reconciled_none(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
            reconciled=True,
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
            reconciled=False,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            [bt1.pk, bt2.pk],
            sorted([bt['id'] for bt in response.data['results']]),
        )

    def test_reconciled(self):
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
            reconciled=True,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
            reconciled=False,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 10),
            'reconciled': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            [bt.pk],
            [b['id'] for b in response.data['results']],
        )

    def test_unreconciled(self):
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
            reconciled=False,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
            reconciled=True,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 10),
            'reconciled': False,
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            [bt.pk],
            [b['id'] for b in response.data['results']],
        )

    def test_date(self):
        bt = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 11),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            [bt.pk],
            [b['id'] for b in response.data['results']],
        )

    def test_order(self):
        bt1 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
        )
        bt2 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
        )
        bt3 = BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            [bt1.pk, bt2.pk, bt3.pk],
            [b['id'] for b in response.data['results']],
        )

    def test_total_none(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)

    def test_total_single(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
            amount=-10,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], -10)

    def test_total_multiple(self):
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
            amount=-10,
        )
        BankTransactionFactory(
            bankaccount=self.bankaccount,
            date=datetime.date(2015, 11, 10),
            amount=-20,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'date': datetime.date(2015, 11, 10),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], -30)
