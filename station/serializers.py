from django.db import transaction
from rest_framework import serializers

from .models import (
    Train,
    TrainType,
    Journey,
    Crew,
    Ticket,
    Order,
    Route,
    Station
)


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ("id", "name", "latitude", "longitude")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(
        read_only=True, slug_field="name"
    )
    destination = serializers.SlugRelatedField(
        read_only=True, slug_field="name"
    )

    class Meta:
        model = Route
        fields = ("id", "source", "destination")


class RouteDetailSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(
        read_only=True, slug_field="name"
    )
    destination = serializers.SlugRelatedField(
        read_only=True, slug_field="name")
    distance_km = serializers.FloatField(
        source="distance", read_only=True
    )

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance_km")


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ("id", "name")


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "cargo_num",
            "places_in_cargo",
            "train_type"
        )


class TrainListSerializer(TrainSerializer):
    train_type = serializers.SlugRelatedField(
        read_only=True, slug_field="name"
    )

    class Meta:
        model = Train
        fields = ("id", "name", "train_type", "image")


class TrainImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "image")


class TrainDetailSerializer(TrainSerializer):
    train_type = serializers.CharField(
        source="train_type.name", read_only=True
    )

    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "train_type",
            "cargo_num",
            "places_in_cargo",
            "image"
        )


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "full_name")


class CrewListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "full_name")


class JourneySerializer(serializers.ModelSerializer):
    departure_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    arrival_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = Journey
        fields = (
            "id",
            "departure_time",
            "arrival_time",
            "route",
            "train",
            "crew"
        )


class JourneyListSerializer(JourneySerializer):
    train_name = serializers.CharField(
        source="train.name", read_only=True
    )
    train_image = serializers.ImageField(
        source="train.image", read_only=True
    )
    route = serializers.CharField(
        source="route.get_route_display"
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Journey
        fields = (
            "id",
            "train_name",
            "train_image",
            "route",
            "departure_time",
            "arrival_time",
            "tickets_available",
        )


class TicketSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        user = validated_data.pop("user", None)

        order, created = Order.objects.get_or_create(user=user)

        validated_data["order"] = order

        ticket = Ticket.objects.create(**validated_data)

        return ticket

    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs)
        ticket_instance = Ticket(**data)
        ticket_instance.clean()

        return data

    class Meta:
        model = Ticket
        fields = ("id", "cargo", "seat", "journey")


class TicketListSerializer(TicketSerializer):
    journey = JourneyListSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "cargo", "seat", "journey")


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("cargo", "seat")


class JourneyDetailSerializer(JourneySerializer):
    train = TrainListSerializer(read_only=True)
    train_image = TrainImageSerializer(read_only=True)
    taken_places = TicketSeatsSerializer(
        source="tickets", many=True, read_only=True
    )
    crew = serializers.SerializerMethodField(read_only=True)
    route = serializers.CharField(
        source="route.get_route_display", read_only=True
    )

    def get_crew(self, obj):
        return [member.full_name for member in obj.crew.all()]

    class Meta:
        model = Journey
        fields = (
            "id",
            "departure_time",
            "arrival_time",
            "route",
            "train",
            "train_image",
            "crew",
            "taken_places",
        )


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(
        many=True, read_only=False, allow_empty=False
    )

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    @staticmethod
    def create(validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
