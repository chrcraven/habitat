from django.urls import path

from . import views

urlpatterns = [
    path("notifications/", views.notification_list),
    path("notifications/mark-all-read/", views.notification_mark_all_read),
    path("notifications/<int:pk>/read/", views.notification_mark_read),
]
