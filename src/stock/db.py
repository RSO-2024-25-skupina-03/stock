from pymongo import MongoClient
from pymongo.errors import OperationFailure
import logging
import os
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)


def create_stock_collection(db):
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


def create_stock_collection_if_not_exists(db):
    try:
        db.validate_collection("stock")
        logger.info("Collection 'stock' available.")
    except OperationFailure:
        # create the stock collection
        create_stock_collection(db)


def connect_to_database(dbname):
    client = MongoClient("mongo", 27017)
    db = client["rso_shop"]
    return db
