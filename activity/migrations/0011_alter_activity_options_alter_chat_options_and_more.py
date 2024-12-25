# Generated by Django 5.1.4 on 2024-12-21 17:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('activity', '0010_chat_last_message_chat_unread_count'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='activity',
            options={'ordering': ['-occured_at'], 'verbose_name_plural': 'Activities'},
        ),
        migrations.AlterModelOptions(
            name='chat',
            options={'ordering': ['-updated_at'], 'verbose_name': 'Chat', 'verbose_name_plural': 'Chats'},
        ),
        migrations.AlterModelOptions(
            name='website',
            options={'verbose_name': 'Website', 'verbose_name_plural': 'Websites'},
        ),
    ]