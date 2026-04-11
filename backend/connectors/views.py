from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from .models import DatabaseConnection
from .serializers import DatabaseConnectionSerializer
from .services import get_connector
import os
import logging

logger = logging.getLogger(__name__)

VALID_PRESET_IDS = [
    'local_postgresql',
    'local_mysql',
    'local_mongodb',
    'local_clickhouse',
    'cloud_mongodb',
    'cloud_postgresql',
]


class DatabaseConnectionViewSet(viewsets.ModelViewSet):
    serializer_class = DatabaseConnectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return DatabaseConnection.objects.all()
        return DatabaseConnection.objects.filter(owner=user)

    @action(detail=False, methods=['get'])
    def presets(self, request):
        """
        Returns available preset connections.
        Credentials are never exposed — only names and types.
        """
        presets = [
            {
                'id': 'local_postgresql',
                'name': 'Local PostgreSQL',
                'db_type': 'postgresql',
                'description': 'PostgreSQL running in Docker',
                'environment': 'local',
            },
            {
                'id': 'local_mysql',
                'name': 'Local MySQL',
                'db_type': 'mysql',
                'description': 'MySQL running in Docker',
                'environment': 'local',
            },
            {
                'id': 'local_mongodb',
                'name': 'Local MongoDB',
                'db_type': 'mongodb',
                'description': 'MongoDB running in Docker',
                'environment': 'local',
            },
            {
                'id': 'local_clickhouse',
                'name': 'Local ClickHouse',
                'db_type': 'clickhouse',
                'description': 'ClickHouse running in Docker',
                'environment': 'local',
            },
        ]

        if os.environ.get('MONGO_DB_URI'):
            presets.append({
                'id': 'cloud_mongodb',
                'name': 'MongoDB Atlas',
                'db_type': 'mongodb',
                'description': 'Cloud MongoDB Atlas cluster',
                'environment': 'cloud',
            })

        if os.environ.get('NEON_DATABASE_URL'):
            presets.append({
                'id': 'cloud_postgresql',
                'name': 'Neon PostgreSQL',
                'db_type': 'postgresql',
                'description': 'Cloud Neon PostgreSQL database',
                'environment': 'cloud',
            })

        return Response(presets)

    @action(detail=False, methods=['post'])
    def connect_preset(self, request):
        """
        Creates a connection from a preset.
        All credentials are read from .env — never from the frontend.
        """
        preset_id = request.data.get('preset_id', '').strip()

        # Improvement 3: Strict validation layer
        if not preset_id:
            return Response(
                {'error': 'preset_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if preset_id not in VALID_PRESET_IDS:
            logger.warning(
                f"Invalid preset_id '{preset_id}' attempted by user {request.user.username}"
            )
            return Response(
                {'error': 'Invalid preset ID.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # All credentials come from environment variables
        preset_configs = {
            'local_postgresql': {
                'db_type': 'postgresql',
                'host': os.environ.get('POSTGRES_HOST', 'db'),
                'port': int(os.environ.get('POSTGRES_PORT', 5432)),
                'database_name': os.environ.get('POSTGRES_DB', 'tapeline'),
                'username': os.environ.get('POSTGRES_USER', 'tapeline'),
                'password': os.environ.get('POSTGRES_PASSWORD', ''),
                'name': 'Local PostgreSQL',
            },
            'local_mysql': {
                'db_type': 'mysql',
                'host': os.environ.get('MYSQL_HOST', 'mysql'),
                'port': int(os.environ.get('MYSQL_PORT', 3306)),
                'database_name': os.environ.get('MYSQL_DATABASE', 'test_mysql'),
                'username': os.environ.get('MYSQL_USER', 'mysqluser'),
                'password': os.environ.get('MYSQL_PASSWORD', ''),
                'name': 'Local MySQL',
            },
            'local_mongodb': {
                'db_type': 'mongodb',
                'host': os.environ.get('MONGO_HOST', 'mongo'),
                'port': int(os.environ.get('MONGO_PORT', 27017)),
                'database_name': os.environ.get('MONGO_INITDB_DATABASE', 'test_mongo'),
                'username': os.environ.get('MONGO_INITDB_ROOT_USERNAME', 'mongoadmin'),
                'password': os.environ.get('MONGO_INITDB_ROOT_PASSWORD', ''),
                'name': 'Local MongoDB',
            },
            'local_clickhouse': {
                'db_type': 'clickhouse',
                'host': os.environ.get('CLICKHOUSE_HOST', 'clickhouse'),
                'port': int(os.environ.get('CLICKHOUSE_PORT', 8123)),
                'database_name': os.environ.get('CLICKHOUSE_DB', 'default'),
                'username': os.environ.get('CLICKHOUSE_USER', 'default'),
                'password': os.environ.get('CLICKHOUSE_PASSWORD', ''),
                'name': 'Local ClickHouse',
            },
            'cloud_mongodb': {
                'db_type': 'mongodb',
                'host': os.environ.get('MONGO_DB_URI', ''),
                'port': 27017,
                'database_name': 'test_mongo',
                'username': 'tapeline',
                'password': '',
                'name': 'MongoDB Atlas',
            },
            'cloud_postgresql': {
                'db_type': 'postgresql',
                'host': os.environ.get('NEON_DATABASE_URL', ''),
                'port': 5432,
                'database_name': 'neondb',
                'username': 'neondb_owner',
                'password': '',
                'name': 'Neon PostgreSQL',
            },
        }

        config = preset_configs.get(preset_id)

        # Check if already connected
        if DatabaseConnection.objects.filter(
            owner=request.user,
            name=config['name']
        ).exists():
            return Response(
                {'error': f'"{config["name"]}" is already connected.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Improvement 1: Password is encrypted automatically
            # by the model's password setter before saving
            connection = DatabaseConnection.objects.create(
                owner=request.user,
                name=config['name'],
                db_type=config['db_type'],
                host=config['host'],
                port=config['port'],
                database_name=config['database_name'],
                username=config['username'],
                password=config['password'],
            )

            logger.info(
                f"User {request.user.username} connected to {config['name']}"
            )

            return Response(
                DatabaseConnectionSerializer(
                    connection,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            # Improvement 2: Log full error internally, return generic message
            logger.error(
                f"Failed to create connection for user {request.user.username}: {str(e)}"
            )
            return Response(
                {'error': 'Failed to create connection. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Tests if a database connection works."""
        connection = self.get_object()
        try:
            connector = get_connector(connection)
            success = connector.test_connection()
            if success:
                logger.info(
                    f"Connection test successful: {connection.name} "
                    f"by {request.user.username}"
                )
                return Response({
                    'success': True,
                    'message': 'Connection successful!'
                })
            else:
                return Response(
                    {'success': False, 'message': 'Connection failed.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            # Log full error internally
            logger.error(
                f"Connection test failed for {connection.name}: {str(e)}"
            )
            # Return generic message to user
            return Response(
                {'success': False, 'message': 'Connection test failed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def tables(self, request, pk=None):
        """Returns a list of tables in the connected database."""
        connection = self.get_object()
        try:
            connector = get_connector(connection)
            tables = connector.get_tables()
            return Response({'tables': tables})
        except Exception as e:
            logger.error(
                f"Failed to get tables for {connection.name}: {str(e)}"
            )
            return Response(
                {'error': 'Failed to retrieve tables.'},
                status=status.HTTP_400_BAD_REQUEST
            )