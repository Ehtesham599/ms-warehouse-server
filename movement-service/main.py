import logging
from flask_restful import Api, Resource
from flask import Flask, request
from datetime import datetime
from database_connector import collection
import json
from bson import json_util, ObjectId
import pika

QUEUE_NAME = 'movement_log'


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


def location_exists(location_id: str) -> bool:
    """This function checks if location id exists by making a GET request to the location service."""
    import requests
    URL = f"http://location-service/{location_id}"

    res = requests.get(URL)
    if res.status_code != 200:
        return False

    return True


def product_exists(product_id: str) -> bool:
    """This function checks if product id exists by making a GET request to the product service."""
    import requests
    URL = f"http://product-service/{product_id}"

    res = requests.get(URL)
    if res.status_code != 200:
        return False

    return True


def publish_message(message: dict, queue_name: str) -> None:
    """A function that publishes a message body of type dict to a rabbitmq queue"""

    # Setup connection with rabbitmq service name defined in docker compose file
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue=queue_name)

    channel.basic_publish(exchange='', routing_key=queue_name, body=message)
    logging.info(f"Sent message to {queue_name} queue.\n Message body: \n{message}")

    connection.close()


class Movements(Resource):
    def get(self, movement_id: str = None):
        """RESTful GET method"""
        try:
            filters = {}

            if movement_id:
                filters.update({'_id': ObjectId(movement_id)})

            # Get movements documents from collection as list
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
            res = generate500response(str(error))
            return res, 500

    def post(self):
        """RESTful POST method"""
        try:
            data = request.get_json()

            from_location = data['from_location']
            to_location = data['to_location']
            product_id = data['product_id']
            quantity = data['quantity']

            if not from_location and not to_location:
                response = generate400response(
                    "Both from_location and to_location cannot be empty.")
                return response, 400

            if from_location:
                if not location_exists(from_location):
                    response = generate400response(
                        "from_location does not exist.")
                    return response, 400

            if to_location:
                if not location_exists(to_location):
                    response = generate400response(
                        "to_location does not exist.")
                    return response, 400

            if not product_id:
                response = generate400response("product_id key required.")
                return response, 400

            if not quantity:
                response = generate400response(
                    "quantity key required/ quantity cannot be zero.")
                return response, 400

            if not isinstance(quantity, int):
                response = generate400response(
                    "quantity must be of type integer.")
                return response, 400

            # Insert single document from user POST body into movement collection
            result = collection.insert_one(data)

            if not result.acknowledged:
                response = generate500response("Database insertion failed while creating a movement record.")
                return response, 500

            publish_message(data, QUEUE_NAME)

            return {
                       "status": 201,
                       "message": "Success",
                       "timestamp": getISOtimestamp(),
                       "result": f"movement with id: {result.inserted_id} created.",
                   }, 201

        except Exception as error:
            response = generate500response(str(error))
            return response, 500


app = Flask(__name__)
api = Api(app)

api.add_resource(Movements, '/', '/<string:movement_id>')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(port=8080, host='0.0.0.0')
