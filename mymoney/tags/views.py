from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from .models import Tag
from .serializers import TagSerializer


class TagViewSet(ModelViewSet):
    model = Tag
    serializer_class = TagSerializer
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('name',)
    ordering = ('name',)
