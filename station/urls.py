from django.urls import path, include
from rest_framework import routers

from .views import (
    TrainViewSet,
    TrainTypeViewSet,
    JourneyViewSet,
    CrewViewSet,
    TicketViewSet,
    OrderViewSet,
    RouteViewSet,
    StationViewSet
)

router = routers.DefaultRouter()

router.register("train_types", TrainTypeViewSet)
router.register("trains", TrainViewSet)
router.register("journeys", JourneyViewSet)
router.register("crew", CrewViewSet)
router.register("tickets", TicketViewSet)
router.register("orders", OrderViewSet)
router.register("routes", RouteViewSet)
router.register("stations", StationViewSet)


urlpatterns = [path("", include(router.urls))]

app_name = "station"
