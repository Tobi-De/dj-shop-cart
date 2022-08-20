from django.contrib import admin

from .models import Product, ProductVariant

admin.site.register(Product)
admin.site.register(ProductVariant)
