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

    # Who triggered this extraction
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='extraction_jobs'
    )

    # Which database connection to pull data from
    connection = models.ForeignKey(
        DatabaseConnection,
        on_delete=models.CASCADE,
        related_name='extraction_jobs'
    )

    # The table or collection to extract data from
    table_name = models.CharField(max_length=255)

    # How many rows to pull per batch (configurable by user)
    batch_size = models.IntegerField(default=100)

    # Current status of this job
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # If the job fails, store the error message here
    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job {self.id} - {self.table_name} ({self.status})"


class ExtractedRecord(models.Model):
    """
    Stores a single row of data extracted from an external database.
    The actual data is stored as JSON so it can hold any structure
    regardless of which database it came from.
    """

    # Which job this record belongs to
    job = models.ForeignKey(
        ExtractionJob,
        on_delete=models.CASCADE,
        related_name='records'
    )

    # The actual data row stored as JSON
    # e.g. {"id": 1, "name": "John", "email": "john@example.com"}
    data = models.JSONField()

    # Whether this record has been edited by the user
    is_edited = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Record {self.id} from Job {self.job.id}"


class StoredFile(models.Model):
    """
    Tracks files (JSON or CSV) that were generated when
    a user submits edited data back to the backend.
    Each file stores the processed data along with metadata.
    """

    FILE_FORMAT_CHOICES = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
    ]

    # Who owns this file
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stored_files'
    )

    # Which job generated this file
    job = models.ForeignKey(
        ExtractionJob,
        on_delete=models.CASCADE,
        related_name='stored_files'
    )

    # The file format (JSON or CSV)
    file_format = models.CharField(
        max_length=10,
        choices=FILE_FORMAT_CHOICES,
        default='json'
    )

    # The actual file stored on disk
    file = models.FileField(upload_to='exports/%Y/%m/%d/')

    # Source metadata - which DB and table this data came from
    source_metadata = models.JSONField(default=dict)

    # Timestamp of when this file was created
    created_at = models.DateTimeField(auto_now_add=True)

    # Access control - which users can see this file
    shared_with = models.ManyToManyField(
        User,
        related_name='shared_files',
        blank=True
    )

    def __str__(self):
        return f"{self.file_format.upper()} file by {self.owner.username} at {self.created_at}"