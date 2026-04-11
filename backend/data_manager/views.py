import json
import csv
import os
from datetime import datetime
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ExtractionJob, ExtractedRecord, StoredFile
from .serializers import ExtractionJobSerializer, ExtractedRecordSerializer, StoredFileSerializer
from connectors.models import DatabaseConnection
from connectors.services import get_connector


class ExtractionJobViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing extraction jobs.
    GET    /api/jobs/              - list all jobs
    POST   /api/jobs/              - create and run a new job
    GET    /api/jobs/{id}/         - get a single job
    GET    /api/jobs/{id}/records/ - get all records for a job
    POST   /api/jobs/{id}/submit/  - submit edited records and save to file
    """

    serializer_class = ExtractionJobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Users see only their own jobs. Admins see all jobs."""
        user = self.request.user
        if user.is_admin():
            return ExtractionJob.objects.all()
        return ExtractionJob.objects.filter(owner=user)

    def create(self, request, *args, **kwargs):
        """
        Creates an extraction job and immediately runs it.
        Pulls data from the specified connection and table,
        stores each row as an ExtractedRecord.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save the job with pending status
        job = serializer.save(owner=request.user, status='pending')

        try:
            # Update status to running
            job.status = 'running'
            job.save()

            # Get the connector for this connection
            connector = get_connector(job.connection)

            # Fetch data from the external database
            rows = connector.fetch_data(
                table_name=job.table_name,
                batch_size=job.batch_size,
                offset=0
            )

            # Save each row as an ExtractedRecord
            for row in rows:
                # Convert any non-serializable values to strings
                clean_row = {k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                           for k, v in row.items()}
                ExtractedRecord.objects.create(job=job, data=clean_row)

            # Mark job as completed
            job.status = 'completed'
            job.save()

            return Response(
                ExtractionJobSerializer(job, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            # If anything goes wrong, mark job as failed
            job.status = 'failed'
            job.error_message = str(e)
            job.save()
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def records(self, request, pk=None):
        """
        Returns all extracted records for a job.
        GET /api/jobs/{id}/records/
        """
        job = self.get_object()
        records = job.records.all()
        serializer = ExtractedRecordSerializer(records, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Submits edited records back to the backend.
        Validates the data, updates the records,
        and saves them as both a DB record and a file (JSON + CSV).
        POST /api/jobs/{id}/submit/
        Body: {"records": [{"id": 1, "data": {...}}, ...], "format": "json"}
        """
        job = self.get_object()
        records_data = request.data.get('records', [])
        file_format = request.data.get('format', 'json')

        if not records_data:
            return Response(
                {'error': 'No records provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update each record in the database
        updated_records = []
        for record_data in records_data:
            try:
                record = ExtractedRecord.objects.get(
                    id=record_data['id'],
                    job=job
                )
                record.data = record_data['data']
                record.is_edited = True
                record.save()
                updated_records.append(record)
            except ExtractedRecord.DoesNotExist:
                return Response(
                    {'error': f"Record {record_data['id']} not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Build source metadata
        source_metadata = {
            'db_type': job.connection.db_type,
            'database_name': job.connection.database_name,
            'table_name': job.table_name,
            'extracted_at': job.created_at.isoformat(),
            'submitted_at': datetime.utcnow().isoformat(),
            'record_count': len(updated_records),
        }

        # Prepare the data for file storage
        data_to_save = [record.data for record in updated_records]

        # Generate file content based on format
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"export_{job.id}_{timestamp}.{file_format}"

        if file_format == 'json':
            file_content = json.dumps({
                'metadata': source_metadata,
                'data': data_to_save
            }, indent=2, default=str)
            file_bytes = file_content.encode('utf-8')

        elif file_format == 'csv':
            import io
            output = io.StringIO()
            if data_to_save:
                writer = csv.DictWriter(output, fieldnames=data_to_save[0].keys())
                writer.writeheader()
                writer.writerows(data_to_save)
            file_bytes = output.getvalue().encode('utf-8')

        else:
            return Response(
                {'error': 'Invalid format. Use json or csv.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save the file to disk and create a StoredFile record
        stored_file = StoredFile.objects.create(
            owner=request.user,
            job=job,
            file_format=file_format,
            source_metadata=source_metadata,
        )
        stored_file.file.save(filename, ContentFile(file_bytes))

        return Response({
            'message': f'Successfully submitted {len(updated_records)} records.',
            'file': StoredFileSerializer(stored_file, context={'request': request}).data
        })


class StoredFileViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing stored files.
    GET    /api/files/              - list accessible files
    GET    /api/files/{id}/         - get a single file
    DELETE /api/files/{id}/         - delete a file
    POST   /api/files/{id}/share/   - share a file with another user
    """

    serializer_class = StoredFileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Admins see all files.
        Regular users see only their own files
        and files shared with them.
        """
        user = self.request.user
        if user.is_admin():
            return StoredFile.objects.all()
        return StoredFile.objects.filter(
            owner=user
        ) | StoredFile.objects.filter(
            shared_with=user
        )

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """
        Shares a file with another user.
        POST /api/files/{id}/share/
        Body: {"username": "john"}
        Only the file owner can share it.
        """
        stored_file = self.get_object()

        # Only the owner can share their file
        if stored_file.owner != request.user and not request.user.is_admin():
            return Response(
                {'error': 'Only the file owner can share this file.'},
                status=status.HTTP_403_FORBIDDEN
            )

        username = request.data.get('username')
        if not username:
            return Response(
                {'error': 'Please provide a username.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from accounts.models import User
        try:
            user_to_share = User.objects.get(username=username)
            stored_file.shared_with.add(user_to_share)
            return Response({
                'message': f'File shared with {username} successfully.'
            })
        except User.DoesNotExist:
            return Response(
                {'error': f'User {username} not found.'},
                status=status.HTTP_404_NOT_FOUND
            )