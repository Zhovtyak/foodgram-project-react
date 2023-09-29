from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import EMAIL_LENGTH, NAME_LENGTH


class User(AbstractUser):
    email = models.EmailField(max_length=EMAIL_LENGTH, unique=True,
                              verbose_name='Почта')
    first_name = models.CharField(max_length=NAME_LENGTH, blank=True,
                                  verbose_name='Имя')
    last_name = models.CharField(max_length=NAME_LENGTH, blank=True,
                                 verbose_name='Фамилия')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(fields=['username', 'email'],
                                    name='username_email_unique')
        ]

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='subscriber',
                             verbose_name='Пользователь')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='creator',
                               verbose_name='Автор')

    class Meta:
        ordering = ['-id']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='subscribe_unique')
        ]

    def clean(self):
        if self.user == self.author:
            raise ValidationError(
                'Пользователь не может подписаться сам на себя.')

    def __str__(self):
        return f"{self.user} - {self.author}"
