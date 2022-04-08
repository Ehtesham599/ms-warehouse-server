import logging
from flask_restful import Api, Resource
from flask import Flask, request
from datetime import datetime
from database_connector import collection
import json
from bson import json_util, ObjectId


def getISOtimestamp() -> str:
    """ A function that generates ISO 8601 timestamp """
    date = datetime.now()
    return date.isoformat()


def generate400response(error: str) -> dict:
    """ A function that generates a '400-Bad Request' message """
    return {
        "status": 400,
        "message": "Bad Request",
        "error": error
    }


def generate500response(error: str) -> dict:
    """ A function that generates a '500-Internal Server Error' message """
    return {
        "status": 500,
        "message": "Internal Server Error",
        "error": error
    }


class Products(Resource):
    def get(self, product_id: str = None):
        """RESTful GET method"""

        try:
            filters = {}

            if product_id:
                filters.update({'_id': ObjectId(product_id)})

            # Get products documents from collection as list
            result_docs = list(collection.find(filters))

            # Convert to JSON
            result = json.loads(json.dumps(
                result_docs, default=json_util.default))

            # Give 404 response if no records found when applied filters
            if filters and not len(result):
                return {
                    "status": 404,
                    "timestamp": getISOtimestamp(),
                    "message": "Resource Not Found",
                }, 404

            return {
                "status": 200,
                "message": "Success",
                "timestamp": getISOtimestamp(),
                "data": result,
                "records_count": len(result)
            }, 200

        except Exception as error:
            res = generate500response(error)
            return res, 500

    def post(self):
        """RESTful POST method"""
        try:

            data = request.get_json()

            product_name = data['product_name']
            product_desc = data['product_description']

            # Prodduct name and description is mandatory
            if not product_name:
                response = generate400response(f"product_name key required.")
                return response, 400

            if not product_desc:
                response = generate400response(f"product_name key required.")
                return response, 400

            # Insert single document from user POST body
            result = collection.insert_one(data)

            if not result.acknowledged:
                response = generate500response("Database insertion failed.")
                return response, 500

            return {
                "status": 201,
                "message": "Success",
                "timestamp": getISOtimestamp(),
                "result": f"product with {result.inserted_id} created.",
            }, 201

        except Exception as error:
            response = generate500response(error)
            return response, 500

    def put(self):
        """RESTful PUT method"""
        try:
            data = request.get_json()

            product_id = data['product_id']
            product_name = data['product_name']
            product_description = data['product_description']

            # Check if product exists in the database
            if not product_id:
                response = generate400response(f"product_id required.")
                return response, 400

            # Check if product name and description is provided
            if not product_name:
                response = generate400response("product_name key required")
                return response, 400

            if not product_description:
                response = generate400response(
                    "product_description key required")
                return response, 400

            # Check if product wit given Id exists in the database
            source_product = collection.find_one({'_id': ObjectId(product_id)})

            if not source_product:
                response = generate400response(
                    f"Product with {product_id} does not exist.")
                return response, 400

            # Pop product_id key from user request body to pass it to update query without changing product_id
            data.pop('product_id', None)

            # Replace single document with user request body
            result = collection.replace_one(
                {'_id': ObjectId(product_id)}, data)

            if not result.acknowledged:
                response = generate500response("Database query failed.")
                return response, 500

            return {
                "status": 201,
                "message": "Success",
                "timestamp": getISOtimestamp(),
                "result": f"Product with {product_id} updated successfully,"
            }, 201

        except Exception as error:
            response = generate500response(error)
            return response, 500


app = Flask(__name__)
api = Api(app)

api.add_resource(Products, '/', '/<string:product_id>')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(port=8080, host='0.0.0.0')
