import psycopg2
import pymysql
import pymongo
import clickhouse_connect
from abc import ABC, abstractmethod


class BaseConnector(ABC):
    @abstractmethod
    def test_connection(self):
        pass

    @abstractmethod
    def get_tables(self):
        pass

    @abstractmethod
    def fetch_data(self, table_name, batch_size=100, offset=0, filters=None, order_by=None, order_dir='asc'):
        pass


class PostgreSQLConnector(BaseConnector):

    def __init__(self, host, port, database_name, username, password):
        self.host = host
        self.port = port
        self.database_name = database_name
        self.username = username
        self.password = password

    def _get_connection(self):
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

    def fetch_data(self, table_name, batch_size=100, offset=0, filters=None, order_by=None, order_dir='asc'):
        conn = self._get_connection()
        cursor = conn.cursor()

        query = f'SELECT * FROM "{table_name}"'
        params = []

        # Build WHERE clause
        if filters:
            allowed_operators = {'=', '!=', '>', '<', '>=', '<=', 'LIKE', 'ILIKE'}
            conditions = []
            for f in filters:
                op = f.get('operator', '=').upper()
                if op not in allowed_operators:
                    op = '='
                conditions.append(f'"{f["column"]}" {op} %s')
                params.append(f['value'])
            query += ' WHERE ' + ' AND '.join(conditions)

        # Build ORDER BY clause
        if order_by:
            direction = 'DESC' if order_dir.lower() == 'desc' else 'ASC'
            query += f' ORDER BY "{order_by}" {direction}'

        # LIMIT and OFFSET
        query += ' LIMIT %s OFFSET %s'
        params.extend([batch_size, offset])

        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]


class MySQLConnector(BaseConnector):

    def __init__(self, host, port, database_name, username, password):
        self.host = host
        self.port = port
        self.database_name = database_name
        self.username = username
        self.password = password

    def _get_connection(self):
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

    def fetch_data(self, table_name, batch_size=100, offset=0, filters=None, order_by=None, order_dir='asc'):
        conn = self._get_connection()
        cursor = conn.cursor()

        query = f'SELECT * FROM `{table_name}`'
        params = []

        # Build WHERE clause
        if filters:
            allowed_operators = {'=', '!=', '>', '<', '>=', '<=', 'LIKE'}
            conditions = []
            for f in filters:
                op = f.get('operator', '=').upper()
                if op not in allowed_operators:
                    op = '='
                conditions.append(f'`{f["column"]}` {op} %s')
                params.append(f['value'])
            query += ' WHERE ' + ' AND '.join(conditions)

        # Build ORDER BY clause
        if order_by:
            direction = 'DESC' if order_dir.lower() == 'desc' else 'ASC'
            query += f' ORDER BY `{order_by}` {direction}'

        # LIMIT and OFFSET
        query += ' LIMIT %s OFFSET %s'
        params.extend([batch_size, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return list(rows)


class MongoDBConnector(BaseConnector):

    def __init__(self, host, port, database_name, username, password):
        self.host = host
        self.port = port
        self.database_name = database_name
        self.username = username
        self.password = password

    def _get_client(self):
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
        client = self._get_client()
        db = client[self.database_name]
        collections = db.list_collection_names()
        client.close()
        return collections

    def fetch_data(self, table_name, batch_size=100, offset=0, filters=None, order_by=None, order_dir='asc'):
        client = self._get_client()
        db = client[self.database_name]
        collection = db[table_name]

        # Build MongoDB filter dict
        mongo_filter = {}
        if filters:
            operator_map = {
                '=':  '$eq',
                '!=': '$ne',
                '>':  '$gt',
                '<':  '$lt',
                '>=': '$gte',
                '<=': '$lte',
            }
            for f in filters:
                op = operator_map.get(f.get('operator', '='), '$eq')
                mongo_filter[f['column']] = {op: f['value']}

        cursor = collection.find(mongo_filter, {'_id': 0}).skip(offset).limit(batch_size)

        # Apply sort
        if order_by:
            direction = pymongo.DESCENDING if order_dir.lower() == 'desc' else pymongo.ASCENDING
            cursor = cursor.sort(order_by, direction)

        documents = list(cursor)
        client.close()
        return documents


class ClickHouseConnector(BaseConnector):

    def __init__(self, host, port, database_name, username, password):
        self.host = host
        self.port = port
        self.database_name = database_name
        self.username = username
        self.password = password

    def _get_client(self):
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

    def fetch_data(self, table_name, batch_size=100, offset=0, filters=None, order_by=None, order_dir='asc'):
        client = self._get_client()

        query = f'SELECT * FROM `{table_name}`'
        params = []

        # Build WHERE clause
        # ClickHouse uses {p0:String} style params for safety
        if filters:
            allowed_operators = {'=', '!=', '>', '<', '>=', '<=', 'LIKE'}
            conditions = []
            for i, f in enumerate(filters):
                op = f.get('operator', '=').upper()
                if op not in allowed_operators:
                    op = '='
                conditions.append(f'`{f["column"]}` {op} {{p{i}:String}}')
                params.append(f['value'])
            query += ' WHERE ' + ' AND '.join(conditions)

        # Build ORDER BY clause
        if order_by:
            direction = 'DESC' if order_dir.lower() == 'desc' else 'ASC'
            query += f' ORDER BY `{order_by}` {direction}'

        query += f' LIMIT {batch_size} OFFSET {offset}'

        param_dict = {f'p{i}': v for i, v in enumerate(params)}
        result = client.query(query, parameters=param_dict)
        columns = result.column_names
        rows = result.result_rows
        return [dict(zip(columns, row)) for row in rows]


def get_connector(db_connection):
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