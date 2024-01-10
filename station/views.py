from django.db.models import Count, F
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser

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
    permission_classes = (
        IsAdminOrIfAuthenticatedReadOnly,
    )


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = (
        IsAdminOrIfAuthenticatedReadOnly,
    )

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer

        if self.action == "retrieve":
            return RouteDetailSerializer

        return RouteSerializer


class TrainTypeViewSet(viewsets.ModelViewSet):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer
    permission_classes = (
        IsAdminOrIfAuthenticatedReadOnly,
    )


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.all()
    serializer_class = TrainSerializer
    permission_classes = (
        IsAdminOrIfAuthenticatedReadOnly,
    )

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer

        if self.action == "retrieve":
            return TrainDetailSerializer

        if self.action == "upload_image":
            return TrainImageSerializer

        return TrainSerializer

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


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    permission_classes = (
        IsAdminOrIfAuthenticatedReadOnly,
    )

    def get_serializer_class(self):
        if self.action == "list":
            return CrewListSerializer

        return CrewSerializer


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = (
        Journey.objects.all()
        .annotate(
            tickets_available=(
                    F("train__cargo_num") * F("train__places_in_cargo")
                    - Count("tickets")
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


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = (
        IsAdminOrIfAuthenticatedReadOnly,
    )

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
            formatted_data.setdefault(
                journey, {}).setdefault(
                    f"cargo: {cargo}", []
                ).append(
                    f"seat: {seat}"
            )

        return formatted_data

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            return Response(
                {
                    "detail": "User must be authenticated to create a ticket."
                },
                status=status.HTTP_403_FORBIDDEN
            )


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (
        IsAdminOrIfAuthenticatedReadOnly,
    )

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

