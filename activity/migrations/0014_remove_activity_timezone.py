# Generated by Django 5.1.4 on 2025-02-28 03:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('activity', '0013_remove_chatmessage_chat_remove_people_timezone_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='activity',
            name='timezone',
        ),
    ]
