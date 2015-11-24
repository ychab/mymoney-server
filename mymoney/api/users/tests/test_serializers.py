from django.test import TestCase, override_settings

from rest_framework.settings import api_settings

from ..factories import UserFactory
from ..serializers import LoginSerializer


class LoginSerializerTestCase(TestCase):

    def test_no_username(self):
        serializer = LoginSerializer(data={'password': 'foo'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_no_password(self):
        serializer = LoginSerializer(data={'username': 'foo'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    @override_settings(LANGUAGE_CODE='en-us')
    def test_not_authenticated(self):
        serializer = LoginSerializer(data={
            'username': 'foo',
            'password': 'foo',
        })
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            'Invalid username or password.',
            serializer.errors[api_settings.NON_FIELD_ERRORS_KEY][0],
        )

    @override_settings(LANGUAGE_CODE='en-us')
    def test_not_active(self):
        user = UserFactory(password='foo', is_active=False)
        serializer = LoginSerializer(data={
            'username': user.username,
            'password': 'foo',
        })
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            'Your account is not active.',
            serializer.errors[api_settings.NON_FIELD_ERRORS_KEY][0],
        )

    def test_authenticated(self):
        user = UserFactory(password='foo', is_active=True)
        serializer = LoginSerializer(data={
            'username': user.username,
            'password': 'foo',
        })
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'], user)
