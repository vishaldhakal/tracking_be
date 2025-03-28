# Generated by Django 5.1.4 on 2024-12-21 15:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activity', '0007_alter_activity_activity_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('visitor_id', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('active', 'Active'), ('closed', 'Closed')], default='active', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('people', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='activity.people')),
                ('website', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='activity.website')),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_admin', models.BooleanField(default=False)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='activity.chat')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
