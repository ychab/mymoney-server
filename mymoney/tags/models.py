from django.db import models
from django.utils.translation import ugettext_lazy as _


class Tag(models.Model):
    name = models.CharField(max_length=128, verbose_name=_('Name'))

    class Meta:
        db_table = 'tags'

    def __str__(self):
        return self.name
