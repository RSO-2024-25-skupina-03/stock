"""Unit tests for the db module."""

# from src.stock.db import (
#     connect_to_database,
#     _create_stock_collection,
#     create_stock_collection_if_not_exists,
# )
from src.stock import db
import pymongo
import pytest


collections = []


def test_connect_to_database():
    """Tests the connect_to_database function."""
    database = db.connect_to_database("mongo", "rso_shop")
    print(database)
    assert database is not None


@pytest.fixture
def mock_validate_collection(monkeypatch):
    def validate_collection(*args, **kwargs):
        return "stock" in collections

    monkeypatch.setattr(
        pymongo.synchronous.database.Database,
        "validate_collection",
        validate_collection,
    )


@pytest.fixture
def mock_create_stock_collection_if_not_exists(monkeypatch):
    def create_stock_collection_if_not_exists(*args, **kwargs):
        global collections
        print(collections)
        collections.append("stock")
        print(collections)

    monkeypatch.setattr(
        db,
        "create_stock_collection_if_not_exists",
        create_stock_collection_if_not_exists,
    )


# @mongomock.patch(servers=(("mongo", 27017),))
def test_create_stock_collection_if_not_exists(
    mock_validate_collection, mock_create_stock_collection_if_not_exists
):
    """Tests the stock_collection_if_not_exists function."""

    global collections

    client = pymongo.MongoClient("mongo")
    database = client["rso_shop"]
    assert "stock" not in collections

    db.create_stock_collection_if_not_exists(database)
    assert "stock" in collections

    collections = []
