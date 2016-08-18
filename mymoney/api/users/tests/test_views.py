from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from ..factories import UserFactory


class UserListTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse('user:user-list')

    def test_access_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_list(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.user.pk)
        self.assertEqual(response.data['username'], self.user.username)


class LoginViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('login')

    def test_access_anonymous(self):
        response = self.client.post(self.url)
        self.assertNotEqual(response.status_code, 403)

    def test_login_failed(self):
        """
        Just assert that exceptions are thrown, not why.
        """
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(response.wsgi_request.user.pk)

    def test_login(self):
        self.client.force_authenticate(None)
        user = UserFactory(password='foo')
        response = self.client.post(self.url, data={
            'username': user.username,
            'password': 'foo',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_response(self):
        self.client.force_authenticate(None)
        user = UserFactory(password='foo')
        response = self.client.post(self.url, data={
            'username': user.username,
            'password': 'foo',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], user.pk)
        self.assertEqual(response.data['username'], user.username)


class LogoutViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('logout')

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_logout(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_anonymous)
