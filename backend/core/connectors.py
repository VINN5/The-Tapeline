from abc import ABC, abstractmethod
import psycopg2
import pymysql
from pymongo import MongoClient
import clickhouse_connect
from django.conf import settings

class BaseConnector(ABC):
    """Abstract base class for all database connectors"""
    
    @abstractmethod
    def connect(self):
        """Return a live connection/cursor"""
        pass

    @abstractmethod
    def execute_query(self, query: str, params=None):
        """Execute query and return results"""
        pass

    @abstractmethod
    def close(self):
        """Close the connection"""
        pass


class PostgreSQLConnector(BaseConnector):
    def __init__(self, config):
        self.config = config
        self.connection = None

    def connect(self):
        self.connection = psycopg2.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.username,
            password=self.config.password,
            dbname=self.config.database_name
        )
        return self.connection.cursor()

    def execute_query(self, query: str, params=None):
        cursor = self.connect()
        cursor.execute(query, params or ())
        if cursor.description:  # SELECT query
            return cursor.fetchall()
        return None

    def close(self):
        if self.connection:
            self.connection.close()


class MySQLConnector(BaseConnector):
    def __init__(self, config):
        self.config = config
        self.connection = None

    def connect(self):
        self.connection = pymysql.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.username,
            password=self.config.password,
            database=self.config.database_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        return self.connection.cursor()

    def execute_query(self, query: str, params=None):
        cursor = self.connect()
        cursor.execute(query, params or ())
        if cursor.description:
            return cursor.fetchall()
        return None

    def close(self):
        if self.connection:
            self.connection.close()


class MongoDBConnector(BaseConnector):
    def __init__(self, config):
        self.config = config
        self.client = None

    def connect(self):
        self.client = MongoClient(
            host=self.config.host,
            port=self.config.port,
            username=self.config.username,
            password=self.config.password,
            authSource=self.config.database_name
        )
        return self.client[self.config.database_name]

    def execute_query(self, query: str, params=None):
        # For MongoDB we usually use collection methods, but for simplicity we support raw query via find()
        db = self.connect()
        # This is simplified - in real use we'd have better query handling
        return list(db.command(query) if isinstance(query, dict) else [])

    def close(self):
        if self.client:
            self.client.close()


class ClickHouseConnector(BaseConnector):
    def __init__(self, config):
        self.config = config
        self.client = None

    def connect(self):
        self.client = clickhouse_connect.get_client(
            host=self.config.host,
            port=self.config.port,
            username=self.config.username,
            password=self.config.password,
            database=self.config.database_name
        )
        return self.client

    def execute_query(self, query: str, params=None):
        result = self.client.query(query, params or {})
        return result.result_rows

    def close(self):
        if self.client:
            self.client.close()


# Factory to get the right connector
def get_connector(config):
    """Returns the correct connector based on db_type"""
    connectors = {
        'postgresql': PostgreSQLConnector,
        'mysql': MySQLConnector,
        'mongodb': MongoDBConnector,
        'clickhouse': ClickHouseConnector,
    }
    connector_class = connectors.get(config.db_type)
    if not connector_class:
        raise ValueError(f"Unsupported database type: {config.db_type}")
    return connector_class(config)