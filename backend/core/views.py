from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import models
from django.contrib.auth import get_user_model

from .models import ConnectionConfig, ExtractionJob, FileStorage
from .serializers import (
    ConnectionConfigSerializer,
    ExtractionJobSerializer,
    FileStorageSerializer,
)
from .connectors import get_connector

User = get_user_model()


class ConnectionConfigViewSet(viewsets.ModelViewSet):
    queryset = ConnectionConfig.objects.all()
    serializer_class = ConnectionConfigSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        connection = self.get_object()
        try:
            connector = get_connector(connection)
            connector.connect()
            connector.close()
            return Response({"status": "success", "message": "Connection successful"})
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=400)


class ExtractionJobViewSet(viewsets.ModelViewSet):
    queryset = ExtractionJob.objects.all()
    serializer_class = ExtractionJobSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        job = self.get_object()
        try:
            connector = get_connector(job.connection)
            results = connector.execute_query(
                job.query or f"SELECT * FROM {job.table_name} LIMIT {job.batch_size}"
            )
            connector.close()

            return Response({
                "job_id": job.id,
                "records_fetched": len(results) if results else 0,
                "data": results[:10]
            })
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class FileStorageViewSet(viewsets.ModelViewSet):
    serializer_class = FileStorageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return FileStorage.objects.all()
        return FileStorage.objects.filter(
            models.Q(created_by=user) | models.Q(shared_with=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        file_obj = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"error": "user_id is required"}, status=400)
        try:
            user_to_share = User.objects.get(id=user_id)
            file_obj.shared_with.add(user_to_share)
            return Response({"status": "shared successfully"})
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        file_obj = self.get_object()
        return Response({
            "file_name": file_obj.file_name,
            "file_path": file_obj.file_path,
            "file_type": file_obj.file_type
        })