# Generated by Django 4.0.6 on 2023-09-02 11:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('back_end', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verification_code',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]
