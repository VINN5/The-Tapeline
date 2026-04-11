import psycopg2
import pymysql
import pymongo
import clickhouse_connect
from abc import ABC, abstractmethod


class BaseConnector(ABC):
    """
    Abstract base class for all database connectors.
    Every connector (PostgreSQL, MySQL, MongoDB, ClickHouse)
    must implement these three methods.
    Think of this as a contract — every connector must be
    able to test its connection, list tables, and fetch data.
    """

    @abstractmethod
    def test_connection(self):
        """Test if the connection works. Returns True or False."""
        pass

    @abstractmethod
    def get_tables(self):
        """Returns a list of table/collection names in the database."""
        pass

    @abstractmethod
    def fetch_data(self, table_name, batch_size=100, offset=0):
        """
        Fetches a batch of data from the specified table.
        batch_size: how many rows to fetch
        offset: how many rows to skip (for pagination)
        Returns a list of dictionaries, one per row.
        """
        pass


class PostgreSQLConnector(BaseConnector):
    """Connector for PostgreSQL databases."""

    def __init__(self, host, port, database_name, username, password):
        self.host = host
        self.port = port
        self.database_name = database_name
        self.username = username
        self.password = password

    def _get_connection(self):
        """
        Creates and returns a PostgreSQL connection.
        Supports both standard and Neon (SSL) connections.
        """
        if 'neon.tech' in self.host or self.host.startswith('postgresql://') or self.host.startswith('postgres://'):
            return psycopg2.connect(self.host)
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.database_name,
            user=self.username,
            password=self.password
        )

    def test_connection(self):
        try:
            conn = self._get_connection()
            conn.close()
            return True
        except Exception:
            return False

    def get_tables(self):
        """Returns all table names in the public schema."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables

    def fetch_data(self, table_name, batch_size=100, offset=0):
        """Fetches rows from a table and returns them as a list of dicts."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f'SELECT * FROM "{table_name}" LIMIT %s OFFSET %s',
            (batch_size, offset)
        )
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]


class MySQLConnector(BaseConnector):
    """Connector for MySQL databases."""

    def __init__(self, host, port, database_name, username, password):
        self.host = host
        self.port = port
        self.database_name = database_name
        self.username = username
        self.password = password

    def _get_connection(self):
        """Creates and returns a MySQL connection."""
        return pymysql.connect(
            host=self.host,
            port=int(self.port),
            database=self.database_name,
            user=self.username,
            password=self.password,
            cursorclass=pymysql.cursors.DictCursor
        )

    def test_connection(self):
        try:
            conn = self._get_connection()
            conn.close()
            return True
        except Exception:
            return False

    def get_tables(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [list(row.values())[0] for row in cursor.fetchall()]
        conn.close()
        return tables

    def fetch_data(self, table_name, batch_size=100, offset=0):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f'SELECT * FROM `{table_name}` LIMIT %s OFFSET %s',
            (batch_size, offset)
        )
        rows = cursor.fetchall()
        conn.close()
        return list(rows)


class MongoDBConnector(BaseConnector):
    """Connector for MongoDB databases."""

    def __init__(self, host, port, database_name, username, password):
        self.host = host
        self.port = port
        self.database_name = database_name
        self.username = username
        self.password = password

    def _get_client(self):
        """
        Creates and returns a MongoDB client.
        Supports both standard and Atlas (SRV) connection strings.
        """
        if self.host.startswith('mongodb+srv://') or self.host.startswith('mongodb://'):
            return pymongo.MongoClient(self.host)
        uri = f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/"
        return pymongo.MongoClient(uri)

    def test_connection(self):
        try:
            client = self._get_client()
            client.server_info()
            client.close()
            return True
        except Exception:
            return False

    def get_tables(self):
        """In MongoDB, tables are called collections."""
        client = self._get_client()
        db = client[self.database_name]
        collections = db.list_collection_names()
        client.close()
        return collections

    def fetch_data(self, table_name, batch_size=100, offset=0):
        """Fetches documents from a MongoDB collection."""
        client = self._get_client()
        db = client[self.database_name]
        collection = db[table_name]
        documents = list(
            collection.find({}, {'_id': 0})
            .skip(offset)
            .limit(batch_size)
        )
        client.close()
        return documents


class ClickHouseConnector(BaseConnector):
    """Connector for ClickHouse databases."""

    def __init__(self, host, port, database_name, username, password):
        self.host = host
        self.port = port
        self.database_name = database_name
        self.username = username
        self.password = password

    def _get_client(self):
        """Creates and returns a ClickHouse client."""
        return clickhouse_connect.get_client(
            host=self.host,
            port=int(self.port),
            database=self.database_name,
            username=self.username,
            password=self.password
        )

    def test_connection(self):
        try:
            client = self._get_client()
            client.ping()
            return True
        except Exception:
            return False

    def get_tables(self):
        client = self._get_client()
        result = client.query('SHOW TABLES')
        return [row[0] for row in result.result_rows]

    def fetch_data(self, table_name, batch_size=100, offset=0):
        client = self._get_client()
        result = client.query(
            f'SELECT * FROM `{table_name}` LIMIT {batch_size} OFFSET {offset}'
        )
        columns = result.column_names
        rows = result.result_rows
        return [dict(zip(columns, row)) for row in rows]


def get_connector(db_connection):
    """
    Factory function — given a DatabaseConnection model instance,
    returns the correct connector class for that database type.
    """
    connectors = {
        'postgresql': PostgreSQLConnector,
        'mysql': MySQLConnector,
        'mongodb': MongoDBConnector,
        'clickhouse': ClickHouseConnector,
    }

    connector_class = connectors.get(db_connection.db_type)

    if not connector_class:
        raise ValueError(f"Unsupported database type: {db_connection.db_type}")

    return connector_class(
        host=db_connection.host,
        port=db_connection.port,
        database_name=db_connection.database_name,
        username=db_connection.username,
        password=db_connection.password
    )