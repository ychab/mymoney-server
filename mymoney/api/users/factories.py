from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

import factory


class UserFactory(factory.DjangoModelFactory):

    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: 'user_%d' % n)
    password = factory.PostGenerationMethodCall('set_password', 'test')
    email = factory.LazyAttribute(lambda o: '%s@example.com' % o.username)

    @factory.post_generation
    def user_permissions(self, create, extracted, **kwargs):

        if create and extracted:
            if extracted == 'all':
                self.user_permissions.set(UserFactory.get_permissions())
            else:
                self.user_permissions.set(
                    Permission.objects.filter(codename__in=extracted))

    @classmethod
    def get_permissions(cls):

        if not hasattr(cls, '_permissions'):
            cls._permissions = Permission.objects.filter(
                content_type__in=ContentType.objects.filter(
                    app_label__in=(
                        'bankaccounts',
                        'banktransactiontags',
                        'banktransactions',
                        'banktransactionschedulers',
                    ),
                ),
            )

        return cls._permissions
