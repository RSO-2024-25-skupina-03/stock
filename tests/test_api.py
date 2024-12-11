"""Unit tests for the api module."""

import pytest
from src.stock import db
from src.stock import api


@pytest.mark.asyncio
async def test_root():
    result = await api.root()
    assert type(result) is dict


# @pytest.mark.asyncio
# async def test_ids():
#     result = await api.ids()
#     assert type(result) is list


# @pytest.fixture
# def mock_(monkeypatch):
#     def validate_collection(*args, **kwargs):
#         return "stock" in collections

#     monkeypatch.setattr(
#         pymongo.synchronous.database.Database,
#         "validate_collection",
#         validate_collection,
#     )


# @pytest.mark.asyncio
# async def test_product_stock():
#     result = await api.product_stock("1")
#     assert type(result) is dict
#     assert result.stock_amount == 0


# @pytest.mark.asyncio
# async def test_generate_test_data():
#     result = await api.generate_test_data()
#     assert type(result) is dict
