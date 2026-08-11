from django.db import models
from accounts.models import User
from connectors.models import DatabaseConnection


class ExtractionJob(models.Model):
    """
    Represents a batch data extraction job.
    When a user wants to pull data from a connected database,
    they create an ExtractionJob specifying how much data to pull.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='extraction_jobs',
        db_index=True          # faster filtering by owner
    )

    connection = models.ForeignKey(
        DatabaseConnection,
        on_delete=models.CASCADE,
        related_name='extraction_jobs',
        db_index=True          # faster filtering by connection
    )

    table_name = models.CharField(max_length=255)

    batch_size = models.IntegerField(default=100)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True          # faster filtering by status
    )

    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # faster ordering
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']          # newest jobs first by default
        indexes = [
            models.Index(fields=['owner', 'status']),      # common combined filter
            models.Index(fields=['owner', 'created_at']),  # common combined sort
        ]

    def __str__(self):
        return f"Job {self.id} - {self.table_name} ({self.status})"


class ExtractedRecord(models.Model):
    """
    Stores a single row of data extracted from an external database.
    The actual data is stored as JSON so it can hold any structure
    regardless of which database it came from.
    """

    job = models.ForeignKey(
        ExtractionJob,
        on_delete=models.CASCADE,
        related_name='records',
        db_index=True          # faster lookup of records by job
    )

    data = models.JSONField()

    is_edited = models.BooleanField(default=False, db_index=True)  # faster filtering edited records

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']      # consistent record ordering
        indexes = [
            models.Index(fields=['job', 'is_edited']),  # common combined filter
        ]

    def __str__(self):
        return f"Record {self.id} from Job {self.job.id}"


class StoredFile(models.Model):
    """
    Tracks files (JSON, CSV, or XLSX) that were generated when
    a user submits edited data back to the backend.
    Each file stores the processed data along with metadata.
    """

    FILE_FORMAT_CHOICES = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),     # added xlsx support
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stored_files',
        db_index=True          # faster filtering by owner
    )

    job = models.ForeignKey(
        ExtractionJob,
        on_delete=models.CASCADE,
        related_name='stored_files',
        db_index=True          # faster lookup of files by job
    )

    file_format = models.CharField(
        max_length=10,
        choices=FILE_FORMAT_CHOICES,
        default='json'
    )

    file = models.FileField(upload_to='exports/%Y/%m/%d/')

    source_metadata = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    shared_with = models.ManyToManyField(
        User,
        related_name='shared_files',
        blank=True
    )

    class Meta:
        ordering = ['-created_at']     # newest files first
        indexes = [
            models.Index(fields=['owner', 'created_at']),  # common combined filter
        ]

    def __str__(self):
        return f"{self.file_format.upper()} file by {self.owner.username} at {self.created_at}"