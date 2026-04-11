from django.contrib import admin
from .models import ExtractionJob, ExtractedRecord, StoredFile


@admin.register(ExtractionJob)
class ExtractionJobAdmin(admin.ModelAdmin):
    """
    Registers ExtractionJob in the admin panel.
    """

    list_display = ['id', 'owner', 'connection', 'table_name', 'batch_size', 'status', 'created_at']
    list_filter = ['status', 'owner']
    search_fields = ['table_name', 'owner__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ExtractedRecord)
class ExtractedRecordAdmin(admin.ModelAdmin):
    """
    Registers ExtractedRecord in the admin panel.
    """

    list_display = ['id', 'job', 'is_edited', 'created_at']
    list_filter = ['is_edited', 'job']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StoredFile)
class StoredFileAdmin(admin.ModelAdmin):
    """
    Registers StoredFile in the admin panel.
    """

    list_display = ['id', 'owner', 'job', 'file_format', 'created_at']
    list_filter = ['file_format', 'owner']
    search_fields = ['owner__username']
    readonly_fields = ['created_at']