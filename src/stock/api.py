from db import connect_to_database, create_stock_collection_if_not_exists
from fastapi import FastAPI
from stock import get_stock_info
import uvicorn

app = FastAPI()


@app.get("/")
async def root():
    """
    Returns a message.
    """
    return {"status": "Stock API online"}


@app.get("/ids")
async def ids() -> list:
    """An endpoint to fetch all product IDs.

    Returns:
        list: A list of product IDs.
    """
    db_conn = connect_to_database("stock")
    product_ids = db_conn["stock"].distinct("product_id")
    return product_ids


@app.get("/{id}")
async def product_stock(product_id) -> dict:
    """An endpoint to fetch stock information for a product.

    Args:
        product_id (str): Product ID.

    Returns:
        dict: An object containing stock information.
    """
    db_conn = connect_to_database("stock")
    stock_info = get_stock_info(db_conn, product_id)
    return stock_info.to_dict()


# TODO protect this endpoint (JWT?)
@app.post("/generate_test_data")
async def generate_test_data():
    """An endpoint to generate test data for the stock collection."""
    db_conn = connect_to_database("stock")

    # create the collection if it doesn't exist yet
    create_stock_collection_if_not_exists(db_conn)

    # insert test data
    db_conn["stock"].insert_many(
        [
            {"product_id": "1", "stock_amount": 10},
            {"product_id": "2", "stock_amount": 20},
            {"product_id": "3", "stock_amount": 30},
            {"product_id": "4", "stock_amount": 0},
        ]
    )
    return {"status": "Test data generated!"}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)
