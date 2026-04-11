from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model that extends Django's built-in User.
    We add a 'role' field to distinguish between Admins and regular Users.
    """

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user'
    )

    def is_admin(self):
        """Returns True if this user is an admin."""
        return self.role == 'admin'

    def __str__(self):
        return f"{self.username} ({self.role})"