"""Shared pytest configuration and fixtures for all tests."""

import pytest

from src.helpers.singleton import SingletonMeta


@pytest.fixture(autouse=True)
def clear_singleton_meta():
    """Automatically clear SingletonMeta instances before each test to prevent test interference."""
    SingletonMeta._instances.clear()
    yield
    SingletonMeta._instances.clear()
