from rso_stock.db import create_stock_collection_if_not_exists
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
