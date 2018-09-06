from django.contrib.auth import get_user_model

import factory

User = get_user_model()


class UserFactory(factory.DjangoModelFactory):

    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'user_{n}'.format(n=n))
    email = factory.LazyAttribute(lambda o: 'test+{username}@example.com'.format(username=o.username))
    password = factory.PostGenerationMethodCall('set_password', 'test')

    @classmethod
    def _setup_next_sequence(cls):
        """
        Use latest sequence in DB, not in memory...
        """
        try:
            return User.objects.latest('pk').pk + 1
        except User.DoesNotExist:
            return 1
