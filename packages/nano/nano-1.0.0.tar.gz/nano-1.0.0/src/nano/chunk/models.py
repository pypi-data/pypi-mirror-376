from __future__ import unicode_literals

from django.db import models


class Chunk(models.Model):
    slug = models.SlugField()
    content = models.TextField()

    class Meta:
        db_table = 'nano_chunk_chunk'

    def __str__(self):
        return self.slug
