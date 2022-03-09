from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class Cart(models.Model):
    items = models.JSONField()
    customer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart - {self.customer}"
