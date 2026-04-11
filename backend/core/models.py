from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class ConnectionConfig(models.Model):
    """Stores connection details for any supported database"""
    TYPE_CHOICES = [
        ('postgresql', 'PostgreSQL'),
        ('mysql', 'MySQL'),
        ('mongodb', 'MongoDB'),
        ('clickhouse', 'ClickHouse'),
    ]

    name = models.CharField(max_length=100)
    db_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField()
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    database_name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='core_connections')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Database Connection"
        verbose_name_plural = "Database Connections"
        unique_together = ['name', 'created_by']

    def __str__(self):
        return f"{self.name} ({self.db_type})"


class ExtractionJob(models.Model):
    """Represents a batch data extraction job"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    connection = models.ForeignKey(ConnectionConfig, on_delete=models.CASCADE, related_name='jobs')
    table_name = models.CharField(max_length=255)
    query = models.TextField(blank=True, null=True)
    batch_size = models.PositiveIntegerField(default=1000)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='core_jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Job {self.id} - {self.connection.name} ({self.status})"


class FileStorage(models.Model):
    """Stores exported files (JSON/CSV) with permission control"""
    job = models.ForeignKey(ExtractionJob, on_delete=models.CASCADE, related_name='files')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=[('json', 'JSON'), ('csv', 'CSV')])
    file_path = models.CharField(max_length=500)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='core_files')
    shared_with = models.ManyToManyField(User, related_name='core_shared_files', blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.file_name