# Generated by Django 4.0.6 on 2023-09-16 14:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('back_end', '0003_alter_user_profile_picture'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='reset_password_code',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]