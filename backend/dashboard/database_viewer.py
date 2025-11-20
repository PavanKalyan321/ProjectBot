#!/usr/bin/env python3
"""
Database Table Viewer Dashboard for DigitalOcean Droplets
Supports PostgreSQL and MySQL databases with SSH tunneling
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from sqlalchemy import create_engine, inspect, text, MetaData, Table
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseViewer:
    """Database viewer for DigitalOcean droplet databases"""

    def __init__(self, config_file: str = None):
        """Initialize database viewer with configuration"""
        if config_file is None:
            config_file = os.path.join(
                os.path.dirname(__file__),
                'db_config.json'
            )

        self.config_file = config_file
        self.connections = {}
        self.engines = {}
        self.load_config()

    def load_config(self) -> None:
        """Load database connections from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.connections = {
                        conn['name']: conn
                        for conn in config.get('connections', [])
                    }
                logger.info(f"Loaded {len(self.connections)} database connections")
            else:
                logger.warning(f"Config file not found: {self.config_file}")
                self.connections = {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.connections = {}

    def get_connection_string(self, conn_name: str) -> Optional[str]:
        """Build SQLAlchemy connection string"""
        if conn_name not in self.connections:
            return None

        conn = self.connections[conn_name]
        db_type = conn['type']
        user = conn['username']
        password = conn['password']
        host = conn['host']
        port = conn['port']
        database = conn['database']

        if db_type == 'postgresql':
            return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
        elif db_type == 'mysql':
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        else:
            logger.error(f"Unsupported database type: {db_type}")
            return None

    def connect(self, conn_name: str) -> Tuple[bool, str]:
        """Connect to a database"""
        try:
            conn_string = self.get_connection_string(conn_name)
            if not conn_string:
                return False, f"Connection '{conn_name}' not found"

            # Create engine with connection pooling
            engine = create_engine(
                conn_string,
                pool_pre_ping=True,  # Verify connections before using
                pool_size=5,
                max_overflow=10,
                pool_recycle=3600  # Recycle connections after 1 hour
            )

            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            self.engines[conn_name] = engine
            logger.info(f"Connected to database: {conn_name}")
            return True, f"Successfully connected to {conn_name}"

        except SQLAlchemyError as e:
            error_msg = f"Database connection error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def disconnect(self, conn_name: str) -> None:
        """Disconnect from a database"""
        if conn_name in self.engines:
            self.engines[conn_name].dispose()
            del self.engines[conn_name]
            logger.info(f"Disconnected from database: {conn_name}")

    def get_tables(self, conn_name: str) -> Tuple[bool, List[Dict], str]:
        """Get list of tables in the database"""
        try:
            if conn_name not in self.engines:
                success, message = self.connect(conn_name)
                if not success:
                    return False, [], message

            engine = self.engines[conn_name]
            inspector = inspect(engine)

            tables_info = []
            for table_name in inspector.get_table_names():
                # Get row count
                try:
                    with engine.connect() as conn:
                        result = conn.execute(
                            text(f"SELECT COUNT(*) FROM {table_name}")
                        )
                        row_count = result.scalar()
                except:
                    row_count = "N/A"

                # Get columns
                columns = inspector.get_columns(table_name)

                tables_info.append({
                    'name': table_name,
                    'row_count': row_count,
                    'column_count': len(columns),
                    'columns': [col['name'] for col in columns]
                })

            logger.info(f"Retrieved {len(tables_info)} tables from {conn_name}")
            return True, tables_info, "Success"

        except SQLAlchemyError as e:
            error_msg = f"Error fetching tables: {str(e)}"
            logger.error(error_msg)
            return False, [], error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, [], error_msg

    def get_table_schema(self, conn_name: str, table_name: str) -> Tuple[bool, List[Dict], str]:
        """Get schema information for a specific table"""
        try:
            if conn_name not in self.engines:
                success, message = self.connect(conn_name)
                if not success:
                    return False, [], message

            engine = self.engines[conn_name]
            inspector = inspect(engine)

            # Get column information
            columns = inspector.get_columns(table_name)

            # Get primary keys
            pk_constraint = inspector.get_pk_constraint(table_name)
            primary_keys = pk_constraint.get('constrained_columns', [])

            # Get indexes
            indexes = inspector.get_indexes(table_name)
            indexed_columns = set()
            for idx in indexes:
                indexed_columns.update(idx['column_names'])

            schema_info = []
            for col in columns:
                schema_info.append({
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col['nullable'],
                    'default': str(col.get('default', '')),
                    'primary_key': col['name'] in primary_keys,
                    'indexed': col['name'] in indexed_columns
                })

            return True, schema_info, "Success"

        except SQLAlchemyError as e:
            error_msg = f"Error fetching schema: {str(e)}"
            logger.error(error_msg)
            return False, [], error_msg

    def get_table_data(
        self,
        conn_name: str,
        table_name: str,
        page: int = 1,
        per_page: int = 50,
        order_by: str = None,
        order_dir: str = 'ASC',
        filters: Dict[str, Any] = None
    ) -> Tuple[bool, Dict, str]:
        """Get paginated data from a table"""
        try:
            if conn_name not in self.engines:
                success, message = self.connect(conn_name)
                if not success:
                    return False, {}, message

            engine = self.engines[conn_name]

            # Build query
            offset = (page - 1) * per_page

            # Base query
            query = f"SELECT * FROM {table_name}"
            count_query = f"SELECT COUNT(*) FROM {table_name}"

            # Add filters if provided
            where_clauses = []
            if filters:
                for col, value in filters.items():
                    if value:
                        where_clauses.append(f"{col} LIKE '%{value}%'")

            if where_clauses:
                where_clause = " AND ".join(where_clauses)
                query += f" WHERE {where_clause}"
                count_query += f" WHERE {where_clause}"

            # Add ordering
            if order_by:
                query += f" ORDER BY {order_by} {order_dir}"

            # Add pagination
            query += f" LIMIT {per_page} OFFSET {offset}"

            # Execute queries
            with engine.connect() as conn:
                # Get total count
                result = conn.execute(text(count_query))
                total_rows = result.scalar()

                # Get data
                df = pd.read_sql(text(query), conn)

            # Convert to JSON-serializable format
            data = df.to_dict('records')
            columns = df.columns.tolist()

            # Convert any datetime objects to strings
            for row in data:
                for key, value in row.items():
                    if pd.isna(value):
                        row[key] = None
                    elif isinstance(value, (datetime, pd.Timestamp)):
                        row[key] = value.strftime('%Y-%m-%d %H:%M:%S')

            result = {
                'data': data,
                'columns': columns,
                'page': page,
                'per_page': per_page,
                'total_rows': total_rows,
                'total_pages': (total_rows + per_page - 1) // per_page
            }

            return True, result, "Success"

        except SQLAlchemyError as e:
            error_msg = f"Error fetching data: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg

    def execute_query(self, conn_name: str, query: str) -> Tuple[bool, Dict, str]:
        """Execute a custom SQL query"""
        try:
            if conn_name not in self.engines:
                success, message = self.connect(conn_name)
                if not success:
                    return False, {}, message

            engine = self.engines[conn_name]

            # Only allow SELECT queries for safety
            if not query.strip().upper().startswith('SELECT'):
                return False, {}, "Only SELECT queries are allowed"

            with engine.connect() as conn:
                df = pd.read_sql(text(query), conn)

            # Convert to JSON-serializable format
            data = df.to_dict('records')
            columns = df.columns.tolist()

            # Convert any datetime objects to strings
            for row in data:
                for key, value in row.items():
                    if pd.isna(value):
                        row[key] = None
                    elif isinstance(value, (datetime, pd.Timestamp)):
                        row[key] = value.strftime('%Y-%m-%d %H:%M:%S')

            result = {
                'data': data,
                'columns': columns,
                'row_count': len(data)
            }

            return True, result, "Success"

        except SQLAlchemyError as e:
            error_msg = f"Query error: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg

    def export_table_csv(self, conn_name: str, table_name: str) -> Tuple[bool, str, str]:
        """Export table data to CSV"""
        try:
            if conn_name not in self.engines:
                success, message = self.connect(conn_name)
                if not success:
                    return False, "", message

            engine = self.engines[conn_name]

            # Read entire table
            query = f"SELECT * FROM {table_name}"
            with engine.connect() as conn:
                df = pd.read_sql(text(query), conn)

            # Generate CSV
            csv_data = df.to_csv(index=False)

            return True, csv_data, "Success"

        except Exception as e:
            error_msg = f"Export error: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg


# Flask Application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize database viewer
db_viewer = DatabaseViewer()


@app.route('/')
def index():
    """Render main dashboard page"""
    return render_template('database_viewer.html')


@app.route('/api/connections', methods=['GET'])
def get_connections():
    """Get list of available database connections"""
    connections = [
        {
            'name': name,
            'type': conn['type'],
            'host': conn['host'],
            'database': conn['database'],
            'connected': name in db_viewer.engines
        }
        for name, conn in db_viewer.connections.items()
    ]
    return jsonify({
        'success': True,
        'connections': connections
    })


@app.route('/api/connect', methods=['POST'])
def connect_database():
    """Connect to a database"""
    data = request.json
    conn_name = data.get('connection_name')

    if not conn_name:
        return jsonify({
            'success': False,
            'message': 'Connection name is required'
        })

    success, message = db_viewer.connect(conn_name)
    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/api/disconnect', methods=['POST'])
def disconnect_database():
    """Disconnect from a database"""
    data = request.json
    conn_name = data.get('connection_name')

    if not conn_name:
        return jsonify({
            'success': False,
            'message': 'Connection name is required'
        })

    db_viewer.disconnect(conn_name)
    return jsonify({
        'success': True,
        'message': f'Disconnected from {conn_name}'
    })


@app.route('/api/tables', methods=['GET'])
def get_tables():
    """Get list of tables in a database"""
    conn_name = request.args.get('connection')

    if not conn_name:
        return jsonify({
            'success': False,
            'message': 'Connection name is required',
            'tables': []
        })

    success, tables, message = db_viewer.get_tables(conn_name)
    return jsonify({
        'success': success,
        'tables': tables,
        'message': message
    })


@app.route('/api/table/schema', methods=['GET'])
def get_table_schema():
    """Get schema for a specific table"""
    conn_name = request.args.get('connection')
    table_name = request.args.get('table')

    if not conn_name or not table_name:
        return jsonify({
            'success': False,
            'message': 'Connection and table name are required',
            'schema': []
        })

    success, schema, message = db_viewer.get_table_schema(conn_name, table_name)
    return jsonify({
        'success': success,
        'schema': schema,
        'message': message
    })


@app.route('/api/table/data', methods=['GET'])
def get_table_data():
    """Get data from a specific table"""
    conn_name = request.args.get('connection')
    table_name = request.args.get('table')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    order_by = request.args.get('order_by')
    order_dir = request.args.get('order_dir', 'ASC')

    if not conn_name or not table_name:
        return jsonify({
            'success': False,
            'message': 'Connection and table name are required',
            'data': {}
        })

    success, data, message = db_viewer.get_table_data(
        conn_name, table_name, page, per_page, order_by, order_dir
    )
    return jsonify({
        'success': success,
        'data': data,
        'message': message
    })


@app.route('/api/query', methods=['POST'])
def execute_query():
    """Execute a custom SQL query"""
    data = request.json
    conn_name = data.get('connection')
    query = data.get('query')

    if not conn_name or not query:
        return jsonify({
            'success': False,
            'message': 'Connection and query are required',
            'data': {}
        })

    success, result, message = db_viewer.execute_query(conn_name, query)
    return jsonify({
        'success': success,
        'data': result,
        'message': message
    })


@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    """Export table to CSV"""
    conn_name = request.args.get('connection')
    table_name = request.args.get('table')

    if not conn_name or not table_name:
        return jsonify({
            'success': False,
            'message': 'Connection and table name are required'
        })

    success, csv_data, message = db_viewer.export_table_csv(conn_name, table_name)

    if success:
        from flask import Response
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={table_name}.csv'
            }
        )
    else:
        return jsonify({
            'success': False,
            'message': message
        })


def run_dashboard(host='0.0.0.0', port=5002):
    """Run the database viewer dashboard"""
    logger.info(f"Starting Database Viewer Dashboard on {host}:{port}")
    logger.info(f"Access the dashboard at: http://localhost:{port}")
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    run_dashboard()
