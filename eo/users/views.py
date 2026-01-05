from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import UserSerializer, UserCreateSerializer
from .serializers import EmailTokenObtainPairSerializer


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


# --- CRUD Users ---
class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()

    def get_permissions(self):
        # Signup public
        if self.request.method.upper() == "POST":
            return [AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method.upper() == "POST":
            return UserCreateSerializer
        return UserSerializer


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer