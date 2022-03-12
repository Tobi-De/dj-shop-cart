from __future__ import annotations

from django.db import models
from django.utils import timezone


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_price(self, *arg, **kwargs):
        return self.price


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variations"
    )
    size = models.IntegerField()
    color = models.CharField(max_length=255)
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.size} - {self.color}"
