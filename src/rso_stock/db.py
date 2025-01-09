from pymongo import MongoClient
from pymongo.errors import OperationFailure
from rso_stock.utils import loki_handler
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(loki_handler)


def _create_stock_collection(db):
    logger.info("Creating collection 'stock'!")
    # TODO check result
    db.create_collection(
        "stock",
        validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["product_id", "stock_amount"],
                "properties": {
                    "product_id": {
                        "bsonType": "string",
                        "description": "must be a string and is required",
                    },
                    "stock_amount": {
                        "bsonType": "int",
                        "description": "must be an integer and is required",
                    },
                },
            }
        },
    )


def _create_products_collection(db):
    logger.info("Creating collection 'products'!")
    db.create_collection(
        "products",
        validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": [
                    "product_id",
                    "seller_id",
                    "name",
                    "price",
                    "image_b64",
                    "description",
                ],
                "properties": {
                    "product_id": {
                        "bsonType": "string",
                        "description": "must be a string and is required",
                    },
                    "seller_id": {
                        "bsonType": "string",
                        "description": "must be a string and is required",
                    },
                    "name": {
                        "bsonType": "string",
                        "description": "must be a string and is required",
                    },
                    "price": {
                        "bsonType": "double",
                        "description": "must be a double and is required",
                    },
                    "image_b64": {
                        "bsonType": "string",
                        "description": "must be a string and is required",
                    },
                    "description": {
                        "bsonType": "string",
                        "description": "must be a string and is required",
                    },
                },
            }
        },
    )


def create_stock_collection_if_not_exists(db):
    try:
        db.validate_collection("stock")
        logger.info("Collection 'stock' available.")
    except OperationFailure:
        # create the stock collection
        _create_stock_collection(db)


def create_products_collection_if_not_exists(db):
    try:
        db.validate_collection("products")
        logger.info("Collection 'products' available.")
    except OperationFailure:
        # create the products collection
        _create_products_collection(db)


def connect_to_database(host, dbname):
    client = MongoClient("mongo", 27017)
    db = client[dbname]
    return db
