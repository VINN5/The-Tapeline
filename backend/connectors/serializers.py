from rest_framework import serializers
from .models import DatabaseConnection


class DatabaseConnectionSerializer(serializers.ModelSerializer):
    """
    Converts DatabaseConnection model instances to/from JSON.
    This is what the API uses to send and receive connection data.
    The password field is write-only for security —
    it can be set but never read back through the API.
    """

    password = serializers.CharField(write_only=True)

    class Meta:
        model = DatabaseConnection
        fields = [
            'id',
            'name',
            'db_type',
            'host',
            'port',
            'database_name',
            'username',
            'password',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        """
        When creating a connection, automatically set the owner
        to the currently logged in user.
        """
        request = self.context.get('request')
        validated_data['owner'] = request.user
        return super().create(validated_data)