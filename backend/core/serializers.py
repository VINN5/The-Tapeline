from rest_framework import serializers
from .models import ConnectionConfig, ExtractionJob, FileStorage
from django.contrib.auth import get_user_model

User = get_user_model()

class ConnectionConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectionConfig
        fields = ['id', 'name', 'db_type', 'host', 'port', 'username', 
                  'database_name', 'created_by', 'created_at', 'is_active']
        read_only_fields = ['created_by', 'created_at']

class ExtractionJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractionJob
        fields = ['id', 'connection', 'table_name', 'query', 'batch_size', 
                  'status', 'created_by', 'created_at', 'completed_at']
        read_only_fields = ['created_by', 'status', 'created_at', 'completed_at']

class FileStorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileStorage
        fields = ['id', 'job', 'file_name', 'file_type', 'file_path', 
                  'file_size', 'created_by', 'shared_with', 'timestamp']
        read_only_fields = ['created_by', 'timestamp']