from django.db import models
from django.utils import timezone


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_length=5, decimal_places=2)
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    size = models.IntegerField()
    color = models.CharField()
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.size} - {self.color}"
