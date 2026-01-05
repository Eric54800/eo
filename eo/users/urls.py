from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserListCreateView,
    UserDetailView,
    EmailTokenObtainPairView,
)

urlpatterns = [
    # CRUD Users
    path("", UserListCreateView.as_view(), name="user-list"),
    path("<int:pk>/", UserDetailView.as_view(), name="user-detail"),

    # JWT login + refresh
    path("login/", EmailTokenObtainPairView.as_view(), name="jwt-login"),
    path("refresh/", TokenRefreshView.as_view(), name="jwt-refresh"),
]