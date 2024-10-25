from db import connect_to_database
from fastapi import FastAPI
from stock import *
import uvicorn

app = FastAPI()


@app.get("/")
async def root():
    """
    Returns a message.
    """
    return {"status": "Stock API online"}


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


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)
