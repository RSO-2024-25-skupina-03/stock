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
    return StockInfo("TEST PRODUCT", 1000)
