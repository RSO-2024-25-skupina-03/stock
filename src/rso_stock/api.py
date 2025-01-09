from rso_stock.db import connect_to_database, create_stock_collection_if_not_exists
from rso_stock.stock_utils import get_stock_info, get_product_info
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
import base64
import uvicorn
import json
import requests
import logging

app = FastAPI()

# metrics
Instrumentator().instrument(app).expose(app)


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
    db_conn = connect_to_database("mongo", "rso_shop")
    product_ids = db_conn["stock"].distinct("product_id")
    return product_ids


@app.get("/stock/{product_id}")
async def product_stock(product_id) -> dict:
    """An endpoint to fetch stock information for a product.

    Args:
        product_id (str): Product ID.

    Returns:
        dict: An object containing stock information.
    """
    db_conn = connect_to_database("mongo", "rso_shop")
    stock_info = get_stock_info(db_conn, product_id)
    return stock_info.to_dict()


@app.get("/info/{product_id}")
async def product_info(product_id) -> dict:
    """An endpoint to fetch product information.

    Args:
        product_id (str): Product ID.

    Returns:
        dict: An object containing product information.
    """
    db_conn = connect_to_database("mongo", "rso_shop")
    product_info = get_product_info(db_conn, product_id)
    return product_info.to_dict()


# TODO protect this endpoint (JWT?)
@app.post("/generate_test_data")
async def generate_test_data():
    """An endpoint to generate test data for the stock collection."""
    db_conn = connect_to_database("mongo", "rso_shop")

    # create the collection if it doesn't exist yet
    create_stock_collection_if_not_exists(db_conn)

    # try to fetch data from the external API
    API_URL = "https://fakestoreapi.com"
    products = []
    stocks = []
    error = False

    for i in range(1, 10):
        try:
            response = requests.get(f"{API_URL}/products/{i}")
            if response.status_code == 200:
                data = response.json()
                logging.info(
                    f"Successfully fetched data from the external api: {json.dumps(data)}"
                )

                image_url = data["image"]
                image_response = requests.get(image_url)
                image_b64 = base64.b64encode(image_response.content)

                product = {
                    "product_id": str(data["id"]),
                    "seller_id": str(data["id"] + 1),
                    "name": data["title"],
                    "description": data["description"],
                    "image_b64": image_b64,
                    "price": data["price"],
                }

                stock = {
                    "product_id": str(data["id"]),
                    "stock_amount": i * 10,
                }

                products.append(product)
                stocks.append(stock)
            else:
                error = True
                logging.error(
                    f"Failed to fetch data from the external api: {response.status_code}"
                )
                break
        except Exception as e:
            error = True
            logging.error(f"Failed to fetch data from the external api: {e}")
            break

    if error:
        products_data = json.load(open("src/rso_stock/test_product_data.json"))
        products = products_data["data"]
        stocks = [{"product_id": str(i), "stock_amount": i * 10} for i in range(1, 10)]

    # insert test data
    db_conn["products"].insert_many(products)
    db_conn["stock"].insert_many(stocks)
    return {"status": "Test data generated!"}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=False)
