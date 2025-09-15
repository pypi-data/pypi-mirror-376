import os
from contextlib import asynccontextmanager
from pathlib import Path
import inspect
from typing import Callable, Any

from metapg.migrations.runner import MigrationRunner
import psycopg
from metapg.pool.config import DatabaseConfig
from pydantic import Field


class DatabaseTestConfig(DatabaseConfig):
    """Extended DatabaseConfig for test environments with ephemeral options."""

    reuse: bool = Field(
        default=False,
        description="Whether to reuse existing test database",
    )

    on_create: list[Callable[[], Any]] = Field(default_factory=list)

    @classmethod
    def from_base_config(
        cls,
        base_config: DatabaseConfig,
        **test_overrides,
    ) -> "DatabaseTestConfig":
        """Create DatabaseTestConfig from base DatabaseConfig with test-specific overrides.

        Args:
            base_config: Base database configuration
            **test_overrides: Test-specific configuration overrides

        Returns:
            DatabaseTestConfig instance
        """
        # Convert base config to dict and update with test overrides
        config_dict = base_config.model_dump()
        config_dict.update(test_overrides)

        return cls(**config_dict)

    @asynccontextmanager
    async def admin_cursor(self, autocommit: bool = False):
        """Get an async cursor connected to the admin database (postgres).

        Args:
            autocommit: Whether to enable autocommit mode (default: False)

        Yields:
            Async cursor for administrative operations
        """

        base_config = self.model_copy()
        base_config.database = "postgres"

        conn = await psycopg.AsyncConnection.connect(
            **base_config.as_connection_kwargs(),
        )
        try:
            await conn.set_autocommit(autocommit)
            async with conn.cursor() as cur:
                yield cur
        finally:
            await conn.close()

    async def exists(self) -> bool:
        """Check if the test database exists.

        Returns:
            True if database exists, False otherwise
        """
        try:
            async with self.admin_cursor() as cur:
                await cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (self.database,),
                )
                return await cur.fetchone() is not None
        except Exception:
            return False

    async def create(self) -> str:
        """Create the test database asynchronously.

        Returns:
            Database URL for the created test database

        Raises:
            RuntimeError: If database creation fails
        """
        try:
            async with self.admin_cursor(autocommit=True) as cur:
                # Create the test database
                await cur.execute(f'CREATE DATABASE "{self.database}"')

            return self.as_url()

        except Exception as e:
            raise RuntimeError(
                f"Failed to create test database '{self.database}': {e}",
            ) from e

    async def drop(self) -> None:
        """Drop the test database asynchronously."""
        try:
            async with self.admin_cursor(autocommit=True) as cur:
                # Terminate active connections
                await cur.execute(
                    """
                        SELECT pg_terminate_backend(pid)
                        FROM pg_stat_activity
                        WHERE datname = %s AND pid != pg_backend_pid()
                    """,
                    (self.database,),
                )

                # Drop the database
                await cur.execute(f'DROP DATABASE IF EXISTS "{self.database}"')
        except Exception as e:
            import warnings

            warnings.warn(f"Failed to drop test database '{self.database}': {e}")

    async def recreate(self) -> None:
        """Recreate the test database by dropping and creating it."""
        await self.drop()
        await self.create()


async def setup_test_databases(
    databases: dict[str, DatabaseTestConfig] | None = None,
) -> dict[str, DatabaseTestConfig]:
    """Set up test databases with the provided configurations.

    Args:
        configs: Dictionary of database name to TestDatabaseConfig mappings

    Returns:
        Dictionary of configured test databases

    Example:
        configs = {
            'main': DatabaseTestConfig.create_ephemeral(os.getenv('DATABASE_URL')),
            'analytics': DatabaseTestConfig.create_ephemeral(os.getenv('ANALYTICS_URL'))
        }
        test_dbs = setup_test_databases(configs)
    """
    if databases is None:
        base_url = os.getenv("DATABASE_URL")
        if base_url:
            databases = {"default": DatabaseTestConfig.from_url(base_url)}
        else:
            raise ValueError(
                "No database configurations provided and DATABASE_URL not set",
            )

    for name, db in databases.items():
        created = False
        if await db.exists():
            if not db.reuse:
                await db.recreate()
                created = True
        else:
            await db.create()
            created = True

        for path in db.migrations_paths:
            await run_migrations(name, path)

        if created:
            for hook in db.on_create:
                await hook() if inspect.iscoroutinefunction(hook) else hook()

    return databases


async def run_migrations(db_name, path):
    db_migrations_dir = Path(path)

    if db_migrations_dir.exists():
        runner = MigrationRunner(db_name, db_migrations_dir)
        status = await runner.get_status()

        if status.pending:
            print(f"Applying {len(status.pending)} migrations to {db_name}...")
            applied = await runner.apply_pending()
            print(f"Applied {len(applied)} migrations to {db_name}")
        else:
            print(f"Database {db_name} is up to date")


async def drop_test_databases(databases: dict[str, DatabaseTestConfig]) -> None:
    """Drop all test databases in the provided configuration dictionary.

    Args:
        databases: Dictionary of database name to DatabaseTestConfig mappings

    Example:
        test_dbs = setup_test_databases(configs)
        # ... run tests ...
        await drop_test_databases(test_dbs)
    """
    for db in databases.values():
        if await db.exists() and not db.reuse:
            await db.drop()
