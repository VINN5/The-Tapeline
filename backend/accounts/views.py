from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """
    Registers a new user.
    POST /api/accounts/register/
    Body: {"username": "john", "email": "john@example.com",
           "password": "pass123", "password2": "pass123", "role": "user"}
    Returns the new user's data and their JWT tokens.
    No authentication required — anyone can register.
    """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens for the new user
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Gets or updates the currently logged in user's profile.
    GET  /api/accounts/profile/ - get profile
    PUT  /api/accounts/profile/ - update profile
    Requires authentication.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Always return the currently logged in user."""
        return self.request.user


class LogoutView(APIView):
    """
    Logs out the user by blacklisting their refresh token.
    POST /api/accounts/logout/
    Body: {"refresh": "<refresh_token>"}
    After this, the refresh token can no longer be used.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully.'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserListView(generics.ListAPIView):
    """
    Lists all users. Admin only.
    GET /api/accounts/users/
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return User.objects.all()
        return User.objects.none()