from rest_framework.routers import DefaultRouter

from django.urls import path

from . import views

router = DefaultRouter()
router.register("properties", views.PropertyViewSet, basename="property")

urlpatterns = [
    path("auth/csrf/", views.csrf),
    path("auth/signup/", views.signup),
    path("auth/login/", views.login_view),
    path("auth/logout/", views.logout_view),
    path("auth/me/", views.me),
] + router.urls
