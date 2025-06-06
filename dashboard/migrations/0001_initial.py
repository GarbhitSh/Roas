# Generated by Django 5.0.6 on 2024-09-04 18:29

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BusStop",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("lat", models.FloatField()),
                ("lng", models.FloatField()),
                ("distance_to_a", models.FloatField()),
                ("distance_to_b", models.FloatField()),
                ("distance_from_route", models.FloatField()),
            ],
        ),
    ]
