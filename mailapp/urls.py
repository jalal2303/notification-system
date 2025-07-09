# from django.urls import path
# from .views import send_notification

# urlpatterns = [
#     path('notify/', send_notification, name="notify"),
# ]
 
from django.urls import path
from .views import send_notification

urlpatterns = [
    path("api/notify/", send_notification),
]
