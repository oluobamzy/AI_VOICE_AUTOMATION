"""
Alembic environment configuration for AI Video Automation Pipeline.

This script configures the Alembic migration environment to work with our
SQLAlchemy models and database configuration.
"""

import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# Import our models and configuration
from app.core.config import settings
from app.db.base_class import Base
from app.models import *  # Import all models

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the database URL from settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Configure naming conventions for constraints
        render_as_batch=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations with database connection.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Configure naming conventions and comparison options
        render_as_batch=True,
        compare_type=True,
        compare_server_default=True,
        # Include object name in constraints
        include_object=include_object,
        # Configure index and constraint naming
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


def include_object(object, name, type_, reflected, compare_to):
    """
    Filter objects to include in migrations.
    """
    # Skip certain objects if needed
    if type_ == "table" and name in ["spatial_ref_sys"]:  # PostGIS system table
        return False
    return True


def process_revision_directives(context, revision, directives):
    """
    Process revision directives to customize migration generation.
    """
    # Customize migration file generation if needed
    pass


async def run_async_migrations() -> None:
    """
    Run migrations in async mode.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Run async migrations
    asyncio.run(run_async_migrations())


# Determine which mode to run in
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()