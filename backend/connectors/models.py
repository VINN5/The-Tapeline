from django.db import models
from accounts.models import User
from .encryption import encrypt_password, decrypt_password


class DatabaseConnection(models.Model):
    DB_TYPE_CHOICES = [
        ('postgresql', 'PostgreSQL'),
        ('mysql', 'MySQL'),
        ('mongodb', 'MongoDB'),
        ('clickhouse', 'ClickHouse'),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='connections'
    )
    name = models.CharField(max_length=255)
    db_type = models.CharField(max_length=20, choices=DB_TYPE_CHOICES)
    host = models.CharField(max_length=255)
    port = models.IntegerField()
    database_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255)

    # Password is stored encrypted — never in plain text
    _password = models.CharField(max_length=512, db_column='password')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def password(self):
        """
        Decrypts and returns the password.
        Only called internally when making actual connections.
        """
        return decrypt_password(self._password)

    @password.setter
    def password(self, value):
        """
        Encrypts the password before storing it.
        Called automatically when you do connection.password = 'something'
        """
        self._password = encrypt_password(value)

    def __str__(self):
        return f"{self.name} ({self.db_type}) - {self.owner.username}"

    class Meta:
        unique_together = ('owner', 'name')