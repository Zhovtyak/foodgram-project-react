import csv
from typing import Any
from django.core.management.base import BaseCommand
from ...models import Ingredient


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any):
        try:
            ingredients_load()
            print('Готово')
        except Exception as error:
            print(error)


def ingredients_load():
    with open('./data/ingredients.csv', encoding='utf-8') as csv_file:
        fieldnames = ['name', 'measurement_unit']
        csv_reader = csv.DictReader(csv_file, fieldnames=fieldnames)
        for row in csv_reader:
            Ingredient.objects.get_or_create(
                name=row['name'],
                measurement_unit=row['measurement_unit']
            )
