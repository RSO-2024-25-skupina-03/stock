from rso_stock.db import (
    create_stock_collection_if_not_exists,
    create_products_collection_if_not_exists,
)
import logging
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)


class StockInfo:
    def __init__(self, product_id, stock_amount):
        self.product_id = product_id
        self.stock_amount = stock_amount

    def to_dict(self):
        return {"product_id": self.product_id, "stock_amount": self.stock_amount}


class ProductInfo:
    def __init__(self, _id, seller_id, name, price, description, image_b64):
        self._id = _id
        self.seller_id = seller_id
        self.name = name
        self.price = price
        self.description = description
        self.image_b64 = image_b64

    def to_dict(self):
        return {
            "_id": self._id,
            "seller_id": self.seller_id,
            "name": self.name,
            "price": self.price,
            "description": self.description,
            "image_b64": self.image_b64,
        }


def get_stock_info(db_conn, product_id) -> StockInfo:
    """Fetches stock information for the product with the
    specified ID from the database using the provided DB connection object.

    Args:
        db_conn (None): The DB cpnnection.
        product_id (str): The product ID.

    Returns:
        StockInfo: An object containing stock information.
    """
    create_stock_collection_if_not_exists(db_conn)

    product_stock = db_conn["stock"].find_one({"product_id": product_id})
    if product_stock is None:
        return StockInfo(product_id, 0)
    else:
        product_id = product_stock["product_id"]
        stock_amount = product_stock["stock_amount"]
        return StockInfo(product_id, stock_amount)


def get_product_info(db_conn, product_id) -> StockInfo:
    """Fetches product information for the product with the
    specified ID from the database using the provided DB connection object.

    Args:
        db_conn (None): The DB connection.
        product_id (str): The product ID.

    Returns:
        ProductInfo: An object containing product information.
    """
    create_products_collection_if_not_exists(db_conn)

    product_info = db_conn["products"].find_one({"_id": product_id})
    if product_info is None:
        return ProductInfo(product_id, None, None, None, None, None)
    else:
        _id = product_info["_id"]
        seller_id = product_info["seller_id"]
        name = product_info["name"]
        price = product_info["price"]
        description = product_info["description"]
        image_b64 = product_info["image_b64"]
        return ProductInfo(_id, seller_id, name, price, description, image_b64)