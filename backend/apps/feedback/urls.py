from django.urls import path

from . import views

urlpatterns = [
    path("feedback/config/", views.feedback_config),
    path("feedback/pull/", views.feedback_pull),
    path("feedback/pull/mark-synced/", views.feedback_mark_synced),
    path("feedback/<int:pk>/resolve/", views.feedback_resolve),
    path("feedback/", views.feedback_list_or_submit),
]
