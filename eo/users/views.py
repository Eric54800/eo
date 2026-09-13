from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    EmailTokenObtainPairSerializer,
)


# --- JWT LOGIN ---
class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


# --- CRUD USERS ---
class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()

    def get_permissions(self):
        # Signup public
        if self.request.method.upper() == "POST":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method.upper() == "POST":
            return UserCreateSerializer
        return UserSerializer


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


# --- CURRENT USER (/api/users/me/) ---
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
