# Generated by Django 2.2.28 on 2025-04-25 06:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('community_app', '0004_auto_20250425_0920'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='postattachment',
            name='is_primary',
        ),
    ]
