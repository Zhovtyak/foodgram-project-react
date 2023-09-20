from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator


class User(AbstractUser):
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['username', 'email'],
                                    name='username_email_unique')
        ]


class Tag(models.Model):
    name = models.CharField(max_length=200, unique=True)
    color = models.CharField(max_length=7, blank=True)
    slug = models.SlugField(unique=True)


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)


class Receipt(models.Model):
    ingredients = models.ManyToManyField(Ingredient,
                                         through='ReceiptIngredient')
    tags = models.ManyToManyField(Tag)
    image = models.ImageField()
    name = models.CharField(max_length=200)
    text = models.TextField()
    cooking_time = models.IntegerField(validators=[MinValueValidator(1)])
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='recipes')


class ReceiptIngredient(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='receipt_ingredient')
    amount = models.PositiveIntegerField()
