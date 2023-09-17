# Generated by Django 4.0.6 on 2023-09-17 22:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('back_end', '0005_rename_reset_password_code_user_password_reset_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=255)),
                ('company', models.CharField(max_length=255)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('message', models.TextField()),
                ('budget', models.CharField(max_length=255)),
            ],
        ),
    ]
