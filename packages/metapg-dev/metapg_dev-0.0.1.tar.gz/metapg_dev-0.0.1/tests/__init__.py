"""Tests for metapg.dev package.

This package contains comprehensive tests for the development utilities
in metapg.dev.testing, including:

- Unit tests for mock objects and database utilities
- Integration tests that work with real PostgreSQL databases
- Test configuration and fixtures

To run only unit tests (no database required):
    pytest tests/ -m "not integration"

To run integration tests (requires DATABASE_URL):
    pytest tests/ -m integration

To run all tests:
    pytest tests/
"""
