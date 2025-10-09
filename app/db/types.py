"""
Database utilities for cross-database compatibility.

This module provides utilities for handling database-specific types and operations
across different database backends (PostgreSQL, SQLite, etc.).
"""

from typing import Any, List, Type
from datetime import datetime
from sqlalchemy import JSON, TypeDecorator, String, DateTime, text
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.sql import func
import json


class ArrayType(TypeDecorator):
    """
    Cross-database ARRAY type that works with both PostgreSQL and SQLite.
    
    For PostgreSQL: Uses native ARRAY type
    For SQLite: Uses JSON serialization
    """
    
    impl = JSON
    cache_ok = True
    
    def __init__(self, item_type=String, **kwargs):
        """
        Initialize ArrayType.
        
        Args:
            item_type: The type of items in the array (e.g., String, Integer)
            **kwargs: Additional arguments
        """
        self.item_type = item_type
        super().__init__(**kwargs)
    
    def load_dialect_impl(self, dialect):
        """Load the appropriate implementation based on the database dialect."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(postgresql.ARRAY(self.item_type))
        else:
            # For SQLite and other databases, use JSON
            return dialect.type_descriptor(JSON())
    
    def process_bind_param(self, value: Any, dialect) -> Any:
        """Process values being sent to the database."""
        if value is None:
            return value
        
        if dialect.name == 'postgresql':
            # PostgreSQL handles arrays natively
            return value
        else:
            # For SQLite, serialize to JSON
            if isinstance(value, list):
                return json.dumps(value)
            return value
    
    def process_result_value(self, value: Any, dialect) -> List[Any]:
        """Process values being returned from the database."""
        if value is None:
            return []
        
        if dialect.name == 'postgresql':
            # PostgreSQL returns the array directly
            return value if isinstance(value, list) else []
        else:
            # For SQLite, deserialize from JSON
            if isinstance(value, str):
                try:
                    result = json.loads(value)
                    return result if isinstance(result, list) else []
                except (json.JSONDecodeError, TypeError):
                    return []
            elif isinstance(value, list):
                return value
            return []


class UUIDType(TypeDecorator):
    """
    Cross-database UUID type that works with both PostgreSQL and SQLite.
    
    For PostgreSQL: Uses native UUID type
    For SQLite: Uses String representation
    """
    
    impl = String
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        """Load the appropriate implementation based on the database dialect."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(postgresql.UUID(as_uuid=True))
        else:
            # For SQLite, use String with length for UUIDs
            return dialect.type_descriptor(String(36))
    
    def process_bind_param(self, value: Any, dialect) -> Any:
        """Process values being sent to the database."""
        if value is None:
            return value
        
        if dialect.name == 'postgresql':
            # PostgreSQL handles UUIDs natively
            return value
        else:
            # For SQLite, convert to string
            return str(value)
    
    def process_result_value(self, value: Any, dialect) -> Any:
        """Process values being returned from the database."""
        if value is None:
            return value
        
        if dialect.name == 'postgresql':
            # PostgreSQL returns UUID objects
            return value
        else:
            # For SQLite, return the string value
            return str(value) if value else None


def get_array_column(item_type=String, **kwargs):
    """
    Helper function to create a cross-database array column.
    
    Args:
        item_type: The type of items in the array
        **kwargs: Additional column arguments
        
    Returns:
        ArrayType instance suitable for the current database
    """
    return ArrayType(item_type, **kwargs)


def get_uuid_column(**kwargs):
    """
    Helper function to create a cross-database UUID column.
    
    Args:
        **kwargs: Additional column arguments
        
    Returns:
        UUIDType instance suitable for the current database
    """
    return UUIDType(**kwargs)


def get_datetime_default():
    """
    Get cross-database compatible datetime default.
    
    Returns:
        Appropriate default for current_timestamp across databases
    """
    # Use Python's datetime.now as default for compatibility
    # This works consistently across all databases
    return datetime.now


def get_timestamp_server_default():
    """
    Get cross-database compatible server-side timestamp default.
    
    Returns:
        Server default that works across databases
    """
    # For SQLite and others, use CURRENT_TIMESTAMP
    # This is more portable than func.now()
    return text('CURRENT_TIMESTAMP')