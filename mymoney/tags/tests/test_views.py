from unittest import mock

from rest_framework.pagination import PageNumberPagination
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from mymoney.core.factories import UserFactory

from ..factories import TagFactory
from ..models import Tag


class ListViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse('tag-list')

    def tearDown(self):
        Tag.objects.all().delete()

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_access_granted(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_order_by_name(self):
        tag1 = TagFactory(name='foo')
        tag2 = TagFactory(name='bar')
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['id'], tag2.pk)
        self.assertEqual(response.data['results'][1]['id'], tag1.pk)

    @mock.patch.object(
        PageNumberPagination, 'page_size', new_callable=mock.PropertyMock)
    def test_pagination(self, size_mock):
        limit = 2
        size_mock.return_value = limit
        total = limit * 2 + 1

        for i in range(0, total):
            TagFactory()

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(total, response.data['count'])
        self.assertFalse(response.data['previous'])
        self.assertIn(self.url + '?page=2', response.data['next'])
        self.assertEqual(len(response.data['results']), limit)

    def test_serializer(self):
        tag = TagFactory()
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['id'], tag.pk)
        self.assertEqual(response.data['results'][0]['name'], tag.name)


class CreateViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse('tag-list')

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url)
        self.assertNotIn(response.status_code, [401, 403])

    def test_name_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('name', response.data)

    def test_create(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={'name': 'foo'})
        self.assertEqual(response.status_code, 201)
        tag = Tag.objects.get(pk=response.data['id'])
        self.assertEqual(tag.name, 'foo')


class RetrieveViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.tag = TagFactory()
        cls.url = reverse('tag-detail', kwargs={'pk': cls.tag.pk})

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_retrieve(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], self.tag.name)


class PartialUpdateViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.tag = TagFactory(name='foo')
        cls.url = reverse('tag-detail', kwargs={
            'pk': cls.tag.pk,
        })

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 401)

    def test_access_granted(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 200)

    def test_partial_update(self):
        self.client.force_authenticate(self.user)

        response = self.client.patch(self.url, data={'name': 'bar'})
        self.assertEqual(response.status_code, 200)
        self.tag.refresh_from_db()
        self.assertEqual(self.tag.name, 'bar')


class DeleteViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.tag = TagFactory()
        cls.url = reverse('tag-detail', kwargs={
            'pk': cls.tag.pk,
        })

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 401)

    def test_delete(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(Tag.DoesNotExist):
            self.tag.refresh_from_db()
