# Generated by Django 3.2.3 on 2023-09-24 18:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_delete_subscribe'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='receipt',
            options={'ordering': ['-id']},
        ),
    ]