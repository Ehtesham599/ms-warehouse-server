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


class Locations(Resource):
    def get(self, location_id: str = None):
        """RESTful GET method"""

        try:
            filters = {}

            if location_id:
                filters.update({'_id': ObjectId(location_id)})

            # Get locations documents from collection as list
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

            location_name = data['location_name']
            location_latitude = data['location_latitude']
            location_longitude = data['location_longitude']

            # Location name and coordinates is mandatory
            if not location_name:
                response = generate400response(f"location_name key required.")
                return response, 400

            if not location_latitude:
                response = generate400response(
                    f"location_latitude key required.")
                return response, 400

            if not location_longitude:
                response = generate400response(
                    f"location_longitude key required.")
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
                "result": f"location with id: {result.inserted_id} created.",
            }, 201

        except Exception as error:
            response = generate500response(error)
            return response, 500

    def put(self):
        """RESTful PUT method"""
        try:
            data = request.get_json()

            location_id = data['location_id']
            location_name = data['location_name']
            location_latitude = data['location_latitude']
            location_longitude = data['location_longitude']

            # Check if product exists in the database
            if not location_id:
                response = generate400response(f"location_id key required.")
                return response, 400

            # Check if product name and description is provided
            if not location_name:
                response = generate400response("location_name key required")
                return response, 400

            if not location_latitude:
                response = generate400response(
                    f"location_latitude key required.")
                return response, 400

            if not location_longitude:
                response = generate400response(
                    f"location_longitude key required.")
                return response, 400

            if not isinstance(location_latitude, float):
                response = generate400response(
                    f"location_latitude key must be of type float.")
                return response, 400

            if not isinstance(location_longitude, float):
                response = generate400response(
                    f"location_longitude key must be of type float.")
                return response, 400

            # Check if product wit given Id exists in the database
            source_location = collection.find_one(
                {'_id': ObjectId(location_id)})

            if not source_location:
                response = generate400response(
                    f"Location with {location_id} does not exist.")
                return response, 400

            # Pop location_id key from user request body to pass it to update query without changing location_id
            data.pop('location_id', None)

            # Replace single document with user request body
            result = collection.replace_one(
                {'_id': ObjectId(location_id)}, data)

            if not result.acknowledged:
                response = generate500response("Database query failed.")
                return response, 500

            return {
                "status": 201,
                "message": "Success",
                "timestamp": getISOtimestamp(),
                "result": f"Location with id: {location_id} updated successfully,"
            }, 201

        except Exception as error:
            response = generate500response(error)
            return response, 500


app = Flask(__name__)
api = Api(app)

api.add_resource(Locations, '/', '/<string:location_id>')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(port=80, host='0.0.0.0')
