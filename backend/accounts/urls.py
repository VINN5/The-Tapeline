from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, ProfileView, LogoutView, UserListView

urlpatterns = [
    # Register a new user
    path('register/', RegisterView.as_view(), name='register'),

    # Login - returns access and refresh tokens
    path('login/', TokenObtainPairView.as_view(), name='login'),

    # Refresh access token using refresh token
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Logout - blacklists refresh token
    path('logout/', LogoutView.as_view(), name='logout'),

    # View/update own profile
    path('profile/', ProfileView.as_view(), name='profile'),

    # List all users (admin only)
    path('users/', UserListView.as_view(), name='users'),
]