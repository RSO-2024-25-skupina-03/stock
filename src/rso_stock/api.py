from rso_stock.db import connect_to_database, create_stock_collection_if_not_exists
from rso_stock.stock_utils import (
    StockInfo,
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


@app.get("/{tenant}/ids")
async def ids(tenant) -> list:
    """An endpoint to fetch all product IDs.

    Args:
        tenant (str): Tenant name.

    Returns:
        list: A list of product IDs.
    """
    logger.info(f"GET /{tenant}/ids")
    db_name = f"rso_shop_{tenant}"
    logger.info(f"Using database: {db_name}")
    db_conn = connect_to_database("mongo", db_name)
    product_ids = db_conn["stock"].distinct("product_id")
    return product_ids


@app.get("/{tenant}/stock/{product_id}")
async def product_stock(tenant, product_id) -> dict:
    """An endpoint to fetch stock information for a product.

    Args:
        tenant (str): Tenant name.
        product_id (str): Product ID.

    Returns:
        dict: An object containing stock information.
    """
    logger.info(f"GET /{tenant}/stock/{product_id}")
    db_name = f"rso_shop_{tenant}"
    logger.info(f"Using database: {db_name}")
    db_conn = connect_to_database("mongo", db_name)
    stock_info = get_stock_info(db_conn, product_id)
    return stock_info.to_dict()


@app.get(
    "/{tenant}/info/{product_id}",
    responses={
        404: {
            "detail": "Product not found",
            "content": {
                "application/json": {"example": {"detail": "Product not found"}}
            },
        }
    },
)
async def product_info(tenant, product_id) -> dict:
    """An endpoint to fetch product information.

    Args:
        tenant (str): Tenant name.
        product_id (str): Product ID.

    Returns:
        dict: An object containing product information.
    """
    logger.info(f"GET /{tenant}/info/{product_id}")
    db_name = f"rso_shop_{tenant}"
    logger.info(f"Using database: {db_name}")
    db_conn = connect_to_database("mongo", db_name)
    product_info = get_product_info(db_conn, product_id)

    if product_info is None:
        logger.warning(f"Product {product_id} not found")
        raise HTTPException(status_code=404, detail="Product not found")

    return product_info.to_dict()


@app.post(
    "/{tenant}/product",
    responses={
        409: {
            "description": "Product already exists",
            "content": {
                "application/json": {"example": {"detail": "Product already exists"}}
            },
        }
    },
)
async def add_product(tenant, product: ProductModel) -> dict:
    """An endpoint to add a product to the database.

    Args:
        tenant (str): Tenant name.
        product (ProductModel): A ProductModel object.

    Returns:
        dict: An object containing product information.
    """
    logger.info(f"POST /{tenant}/product")
    db_name = f"rso_shop_{tenant}"
    logger.info(f"Using database: {db_name}")
    db_conn = connect_to_database("mongo", db_name)

    # check if the product already exists
    existing = db_conn["products"].find_one({"product_id": product.product_id})
    if existing is not None:
        logger.warning("Product already exists")
        raise HTTPException(status_code=409, detail="Product already exists")

    db_conn["products"].insert_one(dict(product))
    return dict(product)


# TODO protect this endpoint (JWT?)
@app.post("/{tenant}/generate_test_data")
async def generate_test_data(tenant):
    """An endpoint to generate test data for the stock collection.

    Args:
        tenant (str): Tenant name.

    Returns:
        str: A message.
    """

    logger.info(f"POST /{tenant}/generate_test_data")
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


@app.put("/{tenant}/stock/{product_id}/{new_value}")
async def update_stock(tenant, product_id, new_value) -> dict:
    """An endpoint to update stock information for a product.

    Args:
        tenant (str): Tenant name.
        product_id (str): Product ID.
        new_value (str): New value.

    Returns:
        dict: An object containing stock information.
    """
    logger.info(f"PUT /{tenant}/stock/{product_id}/{new_value}")

    # check if the product exists
    db_name = f"rso_shop_{tenant}"
    logger.info(f"Using database: {db_name}")
    db_conn = connect_to_database("mongo", db_name)
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
    uvicorn.run(
        "api:app", host="0.0.0.0", root_path="/api/stock", port=8080, reload=False
    )
