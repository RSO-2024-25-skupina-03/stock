from rso_stock.db import connect_to_database, create_stock_collection_if_not_exists
from rso_stock.stock_utils import (
    StockInfo,
    ProductInfo,
    ProductModel,
    get_stock_info,
    get_product_info,
)
from rso_stock.utils import loki_handler
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
import base64
import uvicorn
import json
import requests
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(loki_handler)

app = FastAPI()

# metrics
Instrumentator().instrument(app).expose(app)


@app.get("/")
async def root():
    """
    Returns a message.
    """
    logger.info("GET /")
    return {"status": "Stock API online"}


@app.get("/ids")
async def ids() -> list:
    """An endpoint to fetch all product IDs.

    Returns:
        list: A list of product IDs.
    """
    logger.info("GET /ids")
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
    logger.info(f"GET /stock/{product_id}")
    db_conn = connect_to_database("mongo", "rso_shop")
    stock_info = get_stock_info(db_conn, product_id)
    return stock_info.to_dict()


@app.get(
    "/info/{product_id}",
    responses={
        404: {
            "detail": "Product not found",
            "content": {
                "application/json": {"example": {"detail": "Product not found"}}
            },
        }
    },
)
async def product_info(product_id) -> dict:
    """An endpoint to fetch product information.

    Args:
        product_id (str): Product ID.

    Returns:
        dict: An object containing product information.
    """
    logger.info(f"GET /info/{product_id}")
    db_conn = connect_to_database("mongo", "rso_shop")
    product_info = get_product_info(db_conn, product_id)

    if product_info is None:
        logger.warning(f"Product {product_id} not found")
        raise HTTPException(status_code=404, detail="Product not found")

    return product_info.to_dict()


@app.post(
    "/product",
    responses={
        409: {
            "description": "Product already exists",
            "content": {
                "application/json": {"example": {"detail": "Product already exists"}}
            },
        }
    },
)
async def add_product(product: ProductModel) -> dict:
    """An endpoint to add a product to the database.

    Args:
        product (ProductModel): A ProductModel object.

    Returns:
        dict: An object containing product information.
    """
    logger.info("POST /product")
    db_conn = connect_to_database("mongo", "rso_shop")

    # check if the product already exists
    existing = db_conn["products"].find_one({"product_id": product.product_id})
    if existing is not None:
        logger.warning("Product already exists")
        raise HTTPException(status_code=409, detail="Product already exists")

    db_conn["products"].insert_one(dict(product))
    return dict(product)


# TODO protect this endpoint (JWT?)
@app.post("/generate_test_data")
async def generate_test_data():
    """An endpoint to generate test data for the stock collection."""
    logger.info("POST /generate_test_data")
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
                logger.info(
                    f"Successfully fetched data from the external api: {json.dumps(data)}"
                )

                image_url = data["image"]
                image_response = requests.get(image_url)
                image_b64 = base64.b64encode(image_response.content).decode("ascii")

                product = {
                    "product_id": str(data["id"]),
                    "seller_id": str(data["id"] + 1),
                    "name": data["title"],
                    "description": data["description"],
                    "image_b64": f"data:image/png;base64,{image_b64}",
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
                logger.warning(
                    f"Failed to fetch data from the external api: {response.status_code}"
                )
                break
        except Exception as e:
            error = True
            logger.warning(f"Failed to fetch data from the external api: {e}")
            break

    if error:
        products_data = json.load(open("src/rso_stock/test_product_data.json"))
        products = products_data["data"]
        stocks = [{"product_id": str(i), "stock_amount": i * 10} for i in range(1, 10)]

    # insert test data
    db_conn["products"].insert_many(products)
    db_conn["stock"].insert_many(stocks)
    return {"status": "Test data generated!"}


@app.put("/stock/{product_id}/{new_value}")
async def update_stock(product_id, new_value) -> dict:
    """An endpoint to update stock information for a product.

    Args:
        product_id (str): Product ID.
        new_value (str): New value.

    Returns:
        dict: An object containing stock information.
    """
    logger.info(f"PUT /stock/{product_id}/{new_value}")

    # check if the product exists
    db_conn = connect_to_database("mongo", "rso_shop")
    product_info = get_product_info(db_conn, product_id)
    if product_info is None:
        logger.warning(f"Product {product_id} not found")
        raise HTTPException(status_code=404, detail="Product not found")

    # check if new value is a positive integer
    value = None
    try:
        value = int(new_value)
        if value < 0:
            logger.warning("Non-positive integer")
            raise ValueError
    except ValueError:
        logger.warning("New value is not a non-positive integer")
        raise HTTPException(
            status_code=400, detail="New value must be a positive integer"
        )

    existing = db_conn["stock"].find_one({"product_id": product_id})
    new_stock_info = StockInfo(product_id, value)

    if existing is None:
        # the product with the specified id does not exist,
        # therefore its stock equals to 0
        db_conn["stock"].insert_one({"product_id": product_id, "stock_amount": value})
    else:
        logger.info(f"Found existing stock info for product {product_id}")
        db_conn["stock"].update_one(
            {"product_id": product_id},
            {"$set": {"stock_amount": value}},
        )
    return new_stock_info.to_dict()


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=False)
