from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.core.validators import RegexValidator

from users.models import User
from .constants import (CHARFIELD_MAX_LENGTH, COLOR_LENGTH,
                        MAX_COOKING_TIME, MIN_COOKING_TIME,
                        MIN_AMOUNT, MAX_AMOUNT, HEX_REGEX)


class Tag(models.Model):
    name = models.CharField(max_length=CHARFIELD_MAX_LENGTH, unique=True,
                            verbose_name='Имя')
    color = models.CharField(max_length=COLOR_LENGTH, verbose_name='Цвет',
                             default='#ffffff', validators=[
                                 RegexValidator(regex=HEX_REGEX,
                                                message='Используйте HEX код.')
                                                ])
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return f'{self.name} ({self.slug})'


class Ingredient(models.Model):
    name = models.CharField(max_length=CHARFIELD_MAX_LENGTH,
                            verbose_name='Название')
    measurement_unit = models.CharField(max_length=CHARFIELD_MAX_LENGTH,
                                        verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
                                    name='ingredient_unique')
        ]

    def __str__(self):
        return self.name


class Receipt(models.Model):
    ingredients = models.ManyToManyField(Ingredient,
                                         through='ReceiptIngredient')
    tags = models.ManyToManyField(Tag, verbose_name='Тэги')
    image = models.ImageField(upload_to='images/recipes/',
                              verbose_name='Картинка')
    name = models.CharField(max_length=CHARFIELD_MAX_LENGTH,
                            verbose_name='Название')
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_COOKING_TIME),
                    MaxValueValidator(MAX_COOKING_TIME)],
        verbose_name='Время приготовления')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='recipes', verbose_name='Автор')

    class Meta:
        ordering = ['-id']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name} - {self.author}'


class ReceiptIngredient(models.Model):
    recipe = models.ForeignKey(Receipt, on_delete=models.CASCADE,
                               related_name='receipt_ingredient',
                               verbose_name='Рецепт')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='receipt_ingredient',
                                   verbose_name='Ингредиент')
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(MIN_AMOUNT),
                    MaxValueValidator(MAX_AMOUNT)])

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'

    def __str__(self):
        return f'{self.ingredient} - {self.recipe}'


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name='Пользователь',
                             related_name='favorites')
    recipe = models.ForeignKey(Receipt, on_delete=models.CASCADE,
                               related_name='favorites',
                               verbose_name='Рецепт')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='favorite_unique')
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name='Пользователь',
                             related_name='shopping_carts')
    recipe = models.ForeignKey(Receipt, on_delete=models.CASCADE,
                               related_name='shopping_carts',
                               verbose_name='Рецепт')

    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='shoppingcart_unique')
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'
