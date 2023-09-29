from django.contrib import admin
from django.core.exceptions import ValidationError

from recipes.models import (Tag, Ingredient, ReceiptIngredient,
                            Receipt, Favorite, ShoppingCart)
from .constants import MIN_COOKING_TIME, MAX_COOKING_TIME


class ReceiptIngredientInline(admin.TabularInline):
    model = Receipt.ingredients.through


class ReceiptAdmin(admin.ModelAdmin):
    inlines = [
        ReceiptIngredientInline,
    ]
    list_filter = ('tags',)
    list_display = ('name', 'author',)

    def clean(self):
        cleaned_data = super().clean()
        cooking_time = cleaned_data.get('cooking_time')
        if cooking_time > MIN_COOKING_TIME and cooking_time < MAX_COOKING_TIME:
            raise ValidationError('Неправильное время приготовления')
        if len(cleaned_data.get('ingredients')) == 0:
            raise ValidationError('Надо добавить хотя бы один ингредиент')


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)


admin.site.register(Receipt, ReceiptAdmin)
admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(ReceiptIngredient)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
