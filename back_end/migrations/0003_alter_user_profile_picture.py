# Generated by Django 4.0.6 on 2023-09-16 08:00

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('back_end', '0002_alter_usercsv_csv_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='profile_picture',
            field=cloudinary.models.CloudinaryField(blank=True, default='https://res.cloudinary.com/dl2adjye7/image/upload/rgpqrf6envo22zzgnndfNone', max_length=255, null=True, verbose_name='profile_picture'),
        ),
    ]
