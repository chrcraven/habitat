from rest_framework.routers import DefaultRouter

from django.urls import path

from . import views

router = DefaultRouter()
router.register("properties", views.PropertyViewSet, basename="property")
router.register("org/members", views.MembershipViewSet, basename="org-member")
router.register("org/invitations", views.InvitationViewSet, basename="org-invitation")

urlpatterns = [
    path("auth/csrf/", views.csrf),
    path("auth/signup/", views.signup),
    path("auth/login/", views.login_view),
    path("auth/logout/", views.logout_view),
    path("auth/me/", views.me),
    path("auth/change-password/", views.change_password),
    path("auth/password-reset/", views.password_reset_request),
    path("auth/password-reset/confirm/", views.password_reset_confirm),
    path("org/", views.OrganizationDetailView.as_view(), name="org-detail"),
    path("invitations/<str:token>/", views.invitation_detail, name="invitation-detail"),
    path("invitations/<str:token>/accept/", views.invitation_accept, name="invitation-accept"),
] + router.urls
