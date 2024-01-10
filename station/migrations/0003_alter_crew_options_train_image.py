# Generated by Django 5.0.1 on 2024-01-10 12:21

import station.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("station", "0002_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="crew",
            options={"verbose_name_plural": "crew"},
        ),
        migrations.AddField(
            model_name="train",
            name="image",
            field=models.ImageField(
                null=True, upload_to=station.models.movie_image_file_path
            ),
        ),
    ]
