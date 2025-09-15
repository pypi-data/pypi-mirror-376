"""Pytest configuration and fixtures for Sky backend tests."""

import pytest_asyncio

# Use multipg for async migrations
from metapg.dev.testing import (
    DatabaseTestConfig,
    drop_test_databases,
    setup_test_databases,
)

DATABASES = {
    "default": DatabaseTestConfig(
        database="test-default",
        user="postgres",
        password="password",
        reuse=False,
    ),
    "foo": DatabaseTestConfig(
        database="test-foo",
        user="postgres",
        password="password",
        reuse=True,
    ),
}


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_databases():
    """Set up test database with migrations for integration tests."""
    databases = await setup_test_databases(DATABASES)
    yield
    await drop_test_databases(databases)
