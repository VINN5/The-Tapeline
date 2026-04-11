from rest_framework import serializers
from .models import ExtractionJob, ExtractedRecord, StoredFile


class ExtractionJobSerializer(serializers.ModelSerializer):
    """
    Converts ExtractionJob model instances to/from JSON.
    Shows the owner's username instead of their ID.
    """

    owner = serializers.StringRelatedField(read_only=True)
    records_count = serializers.SerializerMethodField()

    class Meta:
        model = ExtractionJob
        fields = [
            'id',
            'owner',
            'connection',
            'table_name',
            'batch_size',
            'status',
            'error_message',
            'records_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'status', 'error_message', 'created_at', 'updated_at']

    def get_records_count(self, obj):
        """Returns how many records were extracted in this job."""
        return obj.records.count()

    def create(self, validated_data):
        """Automatically set the owner to the currently logged in user."""
        request = self.context.get('request')
        validated_data['owner'] = request.user
        return super().create(validated_data)


class ExtractedRecordSerializer(serializers.ModelSerializer):
    """
    Converts ExtractedRecord model instances to/from JSON.
    """

    class Meta:
        model = ExtractedRecord
        fields = [
            'id',
            'job',
            'data',
            'is_edited',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'job', 'created_at', 'updated_at']


class StoredFileSerializer(serializers.ModelSerializer):
    """
    Converts StoredFile model instances to/from JSON.
    Shows the owner's username and shared_with usernames.
    """

    owner = serializers.StringRelatedField(read_only=True)
    shared_with = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = StoredFile
        fields = [
            'id',
            'owner',
            'job',
            'file_format',
            'file',
            'source_metadata',
            'shared_with',
            'created_at',
        ]
        read_only_fields = ['id', 'owner', 'file', 'created_at']