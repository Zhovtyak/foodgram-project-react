from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from recipes.models import (Favorite, Ingredient, Receipt, ReceiptIngredient,
                            ShoppingCart, Tag)
from .constants import MAX_COOKING_TIME, MIN_COOKING_TIME


class ReceiptIngredientInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super(ReceiptIngredientInlineFormSet, self).clean()
        if any(self.errors):
            return
        if not any(cleaned_data and not cleaned_data.get('DELETE', False)
                   for cleaned_data in self.cleaned_data):
            raise forms.ValidationError(
                'Надо добавить хотя бы один ингредиент')


class ReceiptIngredientInline(admin.TabularInline):
    model = Receipt.ingredients.through
    formset = ReceiptIngredientInlineFormSet


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


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)


admin.site.register(Receipt, ReceiptAdmin)
admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(ReceiptIngredient)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
