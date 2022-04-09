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
            data = request.json()

            product_id = data['product']
            location_id = data['location']
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


app = Flask(__name__)
api = Api(app)

api.add_resource(Balance, '/')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(port=8080, host='0.0.0.0')
