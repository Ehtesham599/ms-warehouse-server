import json
import logging
from datetime import datetime

from bson import json_util
from flask import Flask
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
    def get(self, location_id: str = None, product_id: str = None):
        """RESTful GET method"""
        try:
            filters = {}

            # Apply filters if provided for querying redis/database
            if product_id:
                filters.update({'product_id': product_id})
            if location_id:
                filters.update({'location_id': location_id})

            result_docs = list(collection.find(filters))

            # Convert to JSON
            result = json.loads(json.dumps(
                result_docs, default=json_util.default))

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


app = Flask(__name__)
api = Api(app)

api.add_resource(Balance, '/', '/<string:location_id>', '/<string:product_id>')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(port=8080, host='0.0.0.0')
