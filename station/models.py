import os
import uuid
from geopy.distance import geodesic

from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Station(models.Model):
    name = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name


class Route(models.Model):
    source = models.ForeignKey(
        Station, on_delete=models.CASCADE, related_name="source_routes"
    )
    destination = models.ForeignKey(
        Station, on_delete=models.CASCADE, related_name="destination_routes"
    )

    @property
    def distance(self) -> float:
        source_coordinates = (self.source.latitude, self.source.longitude)
        destination_coordinates = (
            self.destination.latitude,
            self.destination.longitude,
        )

        distance = geodesic(
            source_coordinates, destination_coordinates
        ).kilometers

        return round(distance, 2)

    @property
    def get_route_display(self):
        return f"From {self.source.name} to {self.destination.name}"

    def __str__(self):
        return f"{self.source.name} - {self.destination.name}"

    class Meta:
        unique_together = ("destination", "source")


class TrainType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


def train_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.name)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/trains/", filename)


class Train(models.Model):
    name = models.CharField(max_length=255, unique=True)
    cargo_num = models.IntegerField()
    places_in_cargo = models.IntegerField()
    train_type = models.ForeignKey(
        TrainType,
        on_delete=models.PROTECT,
        related_name="trains",
        null=True
    )
    image = models.ImageField(
        null=True, upload_to=train_image_file_path
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return self.first_name + " " + self.last_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name_plural = "crew"


class Journey(models.Model):
    route = models.ForeignKey(
        Route, on_delete=models.CASCADE, related_name="journey_routes"
    )
    train = models.ForeignKey(
        Train, on_delete=models.CASCADE, related_name="journey_trains"
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(Crew, blank=True)

    def __str__(self):
        return f"{self.train.name} ({self.departure_time})"

    class Meta:
        ordering = ["-departure_time", "train__name"]


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )


class Ticket(models.Model):
    cargo = models.IntegerField()
    seat = models.IntegerField()
    journey = models.ForeignKey(
        Journey, on_delete=models.CASCADE, related_name="tickets"
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="tickets"
    )

    def clean(self):
        for ticket_attr_value, ticket_attr_name, train_attr_name in [
            (self.cargo, "cargo", "cargo_num"),
            (self.seat, "seat", "places_in_cargo"),
        ]:
            count_attrs = getattr(self.journey.train, train_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise ValidationError(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                        f"number must be in available range: "
                        f"(1, {train_attr_name}): "
                        f"(1, {count_attrs})"
                    }
                )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self):
        return f"{str(self.journey)} (cargo: {self.cargo}, seat: {self.seat})"

    class Meta:
        unique_together = ("journey", "cargo", "seat")
        ordering = ["journey", "cargo", "seat"]
