from django.contrib import admin

from .models import (User, Tag, Ingredient, ReceiptIngredient,
                     Receipt, Favorite, ShoppingCart, Subscribe)

admin.site.register(User)
admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Receipt)
admin.site.register(ReceiptIngredient)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
admin.site.register(Subscribe)
