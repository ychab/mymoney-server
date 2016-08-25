from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import ugettext as _

from rest_framework import serializers

from mymoney.api.bankaccounts.serializers import BankAccountSerializer


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError(
                _('Invalid username or password.'))

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email')
        read_only_fields = fields


class UserDetailSerializer(UserSerializer):
    bankaccounts = BankAccountSerializer(many=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('bankaccounts',)
        read_only_fields = fields

    def to_representation(self, instance):
        data = super(UserSerializer, self).to_representation(instance)
        data['permissions'] = [
            perm.codename for perm in instance.user_permissions.all()
        ]
        return data
