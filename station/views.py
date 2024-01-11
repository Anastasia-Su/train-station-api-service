from datetime import datetime

from django.db.models import Count, F
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Train, TrainType, Journey, Crew, Ticket, Order, Route, Station
from .serializers import (
    TrainSerializer,
    TrainListSerializer,
    TrainDetailSerializer,
    TrainImageSerializer,
    TrainTypeSerializer,
    JourneySerializer,
    JourneyListSerializer,
    JourneyDetailSerializer,
    CrewSerializer,
    CrewListSerializer,
    TicketSerializer,
    OrderSerializer,
    OrderListSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouteDetailSerializer,
    StationSerializer,
)
from .permissions import IsAdminOrIfAuthenticatedReadOnly


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all().select_related("source", "destination")
    serializer_class = RouteSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer

        if self.action == "retrieve":
            return RouteDetailSerializer

        return RouteSerializer


class TrainTypeViewSet(viewsets.ModelViewSet):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.all().select_related("train_type")
    serializer_class = TrainSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer

        if self.action == "retrieve":
            return TrainDetailSerializer

        if self.action == "upload_image":
            return TrainImageSerializer

        return TrainSerializer

    def get_queryset(self):
        """Retrieve the movies with filters"""
        type = self.request.query_params.get("train_type")
        queryset = self.queryset

        if type:
            queryset = queryset.filter(train_type__name__icontains=type)

        return queryset.distinct()

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk):
        """Endpoint for uploading image to specific train"""
        train = self.get_object()
        serializer = self.get_serializer(train, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "train_type",
                type=OpenApiTypes.STR,
                description="Filter by train type (ex. ?train_type=pattern)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "list":
            return CrewListSerializer

        return CrewSerializer


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = (
        Journey.objects.select_related("route__source", "route__destination", "train")
        .prefetch_related("crew")
        .annotate(
            tickets_available=(
                F("train__cargo_num") * F("train__places_in_cargo") - Count("tickets")
            )
        )
    )
    serializer_class = JourneySerializer

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer

        if self.action == "retrieve":
            return JourneyDetailSerializer

        return JourneySerializer

    def get_queryset(self):
        date = self.request.query_params.get("date")
        train_id_str = self.request.query_params.get("train")
        print("date", date)
        queryset = self.queryset

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()

            queryset = queryset.filter(departure_time__date=date)

        if train_id_str:
            queryset = queryset.filter(train_id=int(train_id_str))

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "train",
                type=OpenApiTypes.INT,
                description="Filter by train id (ex. ?train=2)",
            ),
            OpenApiParameter(
                "date",
                type=OpenApiTypes.DATE,
                description=("Filter by date of departure " "(ex. ?date=2022-10-23)"),
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related("journey__train")

    serializer_class = TicketSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def list(self, request, *args, **kwargs):
        tickets = self.get_queryset()
        formatted_data = self.format_tickets(tickets)
        return Response(formatted_data)

    def format_tickets(self, tickets):
        formatted_data = {}
        for ticket in tickets:
            cargo = ticket.cargo
            seat = ticket.seat

            journey = str(ticket.journey)
            formatted_data.setdefault(journey, {}).setdefault(
                f"cargo: {cargo}", []
            ).append(f"seat: {seat}")

        return formatted_data

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            return Response(
                {"detail": "User must be authenticated to create a ticket."},
                status=status.HTTP_403_FORBIDDEN,
            )


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related(
        "tickets__journey__train", "tickets__journey__route"
    )
    serializer_class = OrderSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
