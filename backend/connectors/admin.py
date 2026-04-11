from django.contrib import admin
from .models import DatabaseConnection


@admin.register(DatabaseConnection)
class DatabaseConnectionAdmin(admin.ModelAdmin):
    """
    Registers DatabaseConnection in the admin panel.
    Password is excluded from the list display for security.
    """

    list_display = ['name', 'db_type', 'host', 'port', 'database_name', 'owner', 'created_at']
    list_filter = ['db_type', 'owner']
    search_fields = ['name', 'host', 'database_name']
    readonly_fields = ['created_at', 'updated_at']