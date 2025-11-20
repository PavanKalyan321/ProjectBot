"""
Database Connection Manager for Crash Game Analytics
Handles SQLAlchemy setup, session management, and connection pooling
"""

import logging
from typing import Optional, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text, event, pool
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from .config import SQLALCHEMY_CONFIG
from .models import Base

# Setup logging
logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL DATABASE ENGINE & SESSION FACTORY
# ============================================================================

class DatabaseConnection:
    """Singleton pattern for database connection management."""

    _engine = None
    _session_factory = None

    @classmethod
    def initialize(cls, config: dict = None) -> None:
        """
        Initialize database engine and session factory.

        Args:
            config: Optional custom SQLAlchemy configuration
        """
        if cls._engine is not None:
            logger.warning("Database connection already initialized.")
            return

        try:
            config = config or SQLALCHEMY_CONFIG
            cls._engine = create_engine(
                config["url"],
                echo=config.get("echo", False),
                pool_size=config.get("pool_size", 10),
                max_overflow=config.get("max_overflow", 20),
                pool_recycle=config.get("pool_recycle", 3600),
                pool_pre_ping=config.get("pool_pre_ping", True),
                connect_args=config.get("connect_args", {}),
                poolclass=pool.QueuePool,
            )

            # Setup event listeners for connection
            @event.listens_for(cls._engine, "connect")
            def receive_connect(dbapi_conn, connection_record):
                """Enable SSL for PostgreSQL connections."""
                pass  # SSL is handled by connection string

            cls._session_factory = sessionmaker(
                bind=cls._engine,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False
            )

            # Test connection
            cls.test_connection()
            logger.info("✅ Database connection initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {str(e)}")
            raise

    @classmethod
    def test_connection(cls) -> bool:
        """
        Test the database connection.

        Returns:
            bool: True if connection successful
        """
        try:
            if cls._engine is None:
                logger.error("Engine not initialized")
                return False

            with cls._engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("✅ Database connection test passed")
                return True

        except OperationalError as e:
            logger.error(f"❌ Database connection failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during connection test: {str(e)}")
            return False

    @classmethod
    def get_session(cls) -> Session:
        """
        Get a new database session.

        Returns:
            Session: SQLAlchemy session
        """
        if cls._session_factory is None:
            cls.initialize()

        return cls._session_factory()

    @classmethod
    @contextmanager
    def session_context(cls) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.

        Usage:
            with DatabaseConnection.session_context() as session:
                # Do something with session
                pass
        """
        session = cls.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {str(e)}")
            raise
        finally:
            session.close()

    @classmethod
    def create_all_tables(cls) -> None:
        """Create all tables in the database."""
        try:
            if cls._engine is None:
                cls.initialize()

            Base.metadata.create_all(cls._engine)
            logger.info("✅ All tables created successfully")

        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to create tables: {str(e)}")
            raise

    @classmethod
    def drop_all_tables(cls) -> None:
        """Drop all tables from the database (use with caution!)."""
        try:
            if cls._engine is None:
                logger.error("Engine not initialized")
                return

            Base.metadata.drop_all(cls._engine)
            logger.warning("⚠️  All tables dropped from database")

        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to drop tables: {str(e)}")
            raise

    @classmethod
    def get_engine(cls):
        """Get the database engine."""
        if cls._engine is None:
            cls.initialize()
        return cls._engine

    @classmethod
    def close(cls) -> None:
        """Close all database connections."""
        if cls._engine is not None:
            cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
            logger.info("✅ Database connections closed")

# ============================================================================
# INITIALIZATION HELPER
# ============================================================================

def init_db(drop_existing: bool = False) -> None:
    """
    Initialize the database (create tables, seed data, etc).

    Args:
        drop_existing: If True, drop all tables before creating new ones
    """
    logger.info("Initializing database...")

    # Initialize connection
    DatabaseConnection.initialize()

    # Test connection
    if not DatabaseConnection.test_connection():
        raise Exception("Failed to connect to database")

    # Drop tables if requested (careful!)
    if drop_existing:
        logger.warning("⚠️  Dropping existing tables...")
        DatabaseConnection.drop_all_tables()

    # Create tables
    DatabaseConnection.create_all_tables()

    logger.info("✅ Database initialization complete")

# ============================================================================
# QUICK ACCESS FUNCTIONS
# ============================================================================

def get_session() -> Session:
    """Quick access function to get a database session."""
    return DatabaseConnection.get_session()

@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for database operations."""
    with DatabaseConnection.session_context() as session:
        yield session
