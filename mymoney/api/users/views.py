from django.contrib.auth import login, logout

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from .serializers import LoginSerializer, UserDetailSerializer


class UserViewSet(GenericViewSet):
    serializer_class = UserDetailSerializer

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.request.user)
        return Response(serializer.data)


class LoginAPIView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        data = UserDetailSerializer(user).data
        return Response(data)


class LogoutAPIView(APIView):

    def post(self, request, *args, **kwargs):
        logout(request)
        return Response()
