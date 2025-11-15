"""Views for users app."""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema
from .models import User
from .serializers import UserSerializer, UserRegistrationSerializer


class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""
    
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Authentication'],
        summary='Регистрация нового пользователя',
        description='Создание нового пользователя с email и паролем',
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response(
            {
                'message': 'Пользователь успешно зарегистрирован',
                'user': UserSerializer(user).data
            },
            status=status.HTTP_201_CREATED
        )


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """Get or update current user profile."""
    
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Return current user."""
        return self.request.user
    
    @extend_schema(
        tags=['Users'],
        summary='Получить профиль текущего пользователя',
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Users'],
        summary='Обновить профиль текущего пользователя',
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Users'],
        summary='Частично обновить профиль',
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class UserListView(generics.ListAPIView):
    """List all users (for selecting executors, co-executors, etc.)."""
    
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Users'],
        summary='Список всех активных пользователей',
        description='Используется для выбора исполнителей, соисполнителей и наблюдателей',
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
