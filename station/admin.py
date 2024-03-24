from django.contrib import admin
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


admin.site.register(Train)
admin.site.register(TrainType)
admin.site.register(Journey)
admin.site.register(Crew)
admin.site.register(Ticket)
admin.site.register(Order)
admin.site.register(Route)
admin.site.register(Station)
