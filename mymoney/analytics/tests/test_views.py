import datetime

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from mymoney.accounts.factories import AccountFactory
from mymoney.core.factories import UserFactory
from mymoney.tags.factories import TagFactory
from mymoney.transactions.factories import TransactionFactory
from mymoney.transactions.models import Transaction

from ..serializers import RatioInputSerializer


class RatioListViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.account = AccountFactory()
        cls.url = reverse('analytics-ratio-list')

    def tearDown(self):
        Transaction.objects.all().delete()

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

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
        TransactionFactory(
            account=self.account,
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
        TransactionFactory(date=datetime.date(2015, 11, 2), amount=-10)

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, data={
            'type': RatioInputSerializer.SUM_DEBIT,
            'date_start': datetime.date(2015, 11, 1),
            'date_end': datetime.date(2015, 11, 30),
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.data['results'], [])

    def test_status_inactive(self):
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            status=Transaction.STATUS_INACTIVE,
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
        tag = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
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
        tag = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=10,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=10,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
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
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            reconciled=True,
        )
        TransactionFactory(
            account=self.account,
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
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            reconciled=True,
        )
        TransactionFactory(
            account=self.account,
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
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            reconciled=True,
        )
        TransactionFactory(
            account=self.account,
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
        tag = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
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
        tag = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=50,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
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
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 1),
            amount=-10,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 30),
            amount=-10,
        )
        TransactionFactory(
            account=self.account,
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
        TransactionFactory(
            account=self.account,
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
        tag = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
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
        tag1 = TagFactory()
        tag2 = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=tag1,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=tag2,
        )
        TransactionFactory(
            account=self.account,
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
        tag = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
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
        tag = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
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
        tag = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-80,
            tag=TagFactory(),
        )
        TransactionFactory(
            account=self.account,
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
        TransactionFactory(
            account=self.account,
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
        tag = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
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
        tag = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
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
        tag = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=TagFactory(),
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
        tag = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
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
        tag = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-20,
            tag=TagFactory(),
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=TagFactory(),
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
        TransactionFactory(
            account=self.account,
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
        tag = TagFactory()
        TransactionFactory(
            account=self.account,
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
        tag = TagFactory()
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=TagFactory(),
        )
        TransactionFactory(
            account=self.account,
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
        TransactionFactory(
            account=self.account,
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
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=TagFactory(),
        )
        TransactionFactory(
            account=self.account,
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
        tag = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=tag,
        )
        TransactionFactory(
            account=self.account,
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
        tag1 = TagFactory()
        tag2 = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-150,
            tag=tag1,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=tag2,
        )
        TransactionFactory(
            account=self.account,
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
        tag1 = TagFactory()
        tag2 = TagFactory()

        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=150,
            tag=tag1,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=50,
            tag=tag2,
        )
        TransactionFactory(
            account=self.account,
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
        cls.tag = TagFactory()
        cls.account = AccountFactory()
        cls.url = reverse('analytics-ratio-summary')

    def tearDown(self):
        Transaction.objects.all().delete()

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

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
        TransactionFactory(
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
        bt1 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 1),
            amount=-30,
            tag=self.tag,
        )
        bt2 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 30),
            amount=-20,
            tag=self.tag,
        )
        TransactionFactory(
            account=self.account,
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
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            status=Transaction.STATUS_INACTIVE,
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
        bt = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            tag=self.tag,
        )
        TransactionFactory(
            account=self.account,
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
        bt = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=10,
            tag=self.tag,
        )
        TransactionFactory(
            account=self.account,
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
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            reconciled=True,
            tag=self.tag,
        )
        TransactionFactory(
            account=self.account,
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
        bt = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            reconciled=True,
            tag=self.tag,
        )
        TransactionFactory(
            account=self.account,
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
        bt = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-10,
            reconciled=False,
            tag=self.tag,
        )
        TransactionFactory(
            account=self.account,
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
        bt1 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=self.tag,
        )
        bt2 = TransactionFactory(
            account=self.account,
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
        bt1 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=50,
            tag=self.tag,
        )
        bt2 = TransactionFactory(
            account=self.account,
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
        bt = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=None,
        )
        TransactionFactory(
            account=self.account,
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
        bt = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=self.tag,
        )
        TransactionFactory(
            account=self.account,
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
        bt1 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=self.tag,
        )
        bt2 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 3),
            amount=-50,
            tag=self.tag,
        )
        bt3 = TransactionFactory(
            account=self.account,
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
        bt1 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=self.tag,
        )
        bt2 = TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-50,
            tag=self.tag,
        )
        bt3 = TransactionFactory(
            account=self.account,
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
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-30,
            tag=self.tag,
        )
        TransactionFactory(
            account=self.account,
            date=datetime.date(2015, 11, 2),
            amount=-40,
            tag=self.tag,
        )
        TransactionFactory(
            account=self.account,
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
