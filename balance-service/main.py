import json
import logging
from datetime import datetime

from bson import json_util
from flask import Flask, request
from flask_restful import Api, Resource

from database_connector import collection


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


class Balance(Resource):
    def get(self):
        """RESTful GET method"""
        try:
            # Get all documents in the collection
            result_docs = list(collection.find())

            # Convert to JSON
            result = json.loads(json.dumps(
                result_docs, default=json_util.default))

            return {
                       "status": 200,
                       "message": "Success",
                       "timestamp": getISOtimestamp(),
                       "data": result,
                       "records_count": len(result)
                   }, 200

        except Exception as error:
            res = generate500response(str(error))
            return res, 500

    def post(self):
        """RESTful POST method"""
        try:
            data = request.get_json()

            product_id = data['product_id']
            location_id = data['location_id']
            qty = data['qty']

            if not product_id:
                res = generate400response("product_id key required.")
                return res, 400

            if not location_id:
                res = generate400response("location_id key required.")
                return res, 400

            if not int(qty):
                res = generate400response("qty is required and must be greater than zero.")
                return res, 400

            # Insert single document from POST body
            result = collection.insert_one(data)

            if not result.acknowledged:
                response = generate500response("Database insertion failed.")
                return response, 500

            return {
                       "status": 201,
                       "message": "Success",
                       "timestamp": getISOtimestamp()
                   }, 201

        except Exception as error:
            res = generate500response(str(error))
            return res, 500

    def put(self):
        """RESTful PUT method"""

        try:
            data = request.get_json()

            product_id = data['product_id']
            location_id = data['location_id']
            qty = data['qty']

            # Check if location exists in the database
            if not location_id:
                response = generate400response(f"location_id key required.")
                return response, 400

            # Check if location exists in the database
            if not product_id:
                response = generate400response(f"product_id key required.")
                return response, 400

            if not qty:
                response = generate400response(f"qty key required.")
                return response, 400

            if int(qty) <= 0:
                response = generate400response(f"qty cannot be less than or equal to zero.")
                return response, 400

            # Check if record exists with given product and location id
            filters = {
                'product_id': product_id,
                'location_id': location_id
            }

            source_record = collection.find_one(filters)
            if not source_record:
                response = generate400response(
                    f"Record with {product_id} and {location_id} does not exist.")
                return response, 400

            # Replace single document with request body
            result = collection.replace_one(filters, data)

            if not result.acknowledged:
                response = generate500response("Database query failed.")
                return response, 500

            return {
                "status": 201,
                "message": "Success",
                "timestamp": getISOtimestamp(),
                "result": "Record updated successfully"
            }, 201

        except Exception as error:
            response = generate500response(str(error))
            return response, 500


    def delete(self):
        """RESTful DELETE method"""
        try:
            data = request.json()

            product_id = data['product_id']
            location_id = data['location_id']

            if not product_id:
                res = generate400response("product_id key required")
                return res, 400

            if not location_id:
                res = generate400response("location_id key required")
                return res, 400

            filters = {
                'product_id': product_id,
                'location_id': location_id
            }

            result = collection.delete_one(filters)

            if not result.acknowledged:
                response = generate500response("Database query failed.")
                return response, 500

            return {
                       "status": 204,
                       "message": "Success",
                       "timestamp": getISOtimestamp(),
                       "result": "Resource deleted successfully."
                   }, 204

        except Exception as error:
            res = generate500response(str(error))
            return res, 500


app = Flask(__name__)
api = Api(app)

api.add_resource(Balance, '/')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(port=80, host='0.0.0.0')
