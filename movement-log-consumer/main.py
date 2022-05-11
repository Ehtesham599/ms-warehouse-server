import logging
import pika
import requests
import time
import pickle
from database_connector import *

QUEUE_NAME = 'movement_log'


def main():
    logging.basicConfig(level=logging.INFO)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME)

    def callback(ch, method, properties, body):
        logging.info("Received %s" % str(body))
        try:
            allocate_product(pickle.loads(body))
        except Exception as error:
            logging.info(str(error))

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)

    logging.info('Waiting for messages...')
    channel.start_consuming()


def product_exists_at_location(product_id: str, location_id: str) -> bool:
    """This function checks if product exists at given location."""
    filters = {
        'product_id': product_id,
        'location_id': location_id
    }

    result_doc = balance_collection.find_one(filters)
    if not result_doc:
        return False

    return True


def get_product_qty(product_id: str, location_id: str) -> int:
    filters = {
        'product_id': product_id,
        'location_id': location_id
    }

    result_doc = balance_collection.find_one(filters)
    return int(result_doc['qty'])


def allocate_product(data: dict) -> None:
    """This function reads the product movement data and allocates quantity in corresponding location based on type
    of movement.
    - if from location is not provided and to location is provided, this means a product is being added to the location
    and vice-versa when from location is provided and to location is not (product being removed).
    - if both from and to locations are provided, quantity is updated in the overall balance data.
    """

    from_location = data['from_location']
    to_location = data['to_location']
    product_id = data['product_id']
    quantity = data['quantity']

    BALANCE_SERVICE_URL = f'http://balance-service'

    # Product moving into a location
    if not from_location and to_location:
        if product_exists_at_location(product_id, to_location):
            from_location_current_qty = get_product_qty(product_id, to_location)

            final_qty = from_location_current_qty + quantity
            post_obj = {
                'product_id': product_id,
                'location_id': to_location,
                'qty': final_qty
            }

            res = requests.put(url=BALANCE_SERVICE_URL, json=post_obj)
            if res.status_code == 201:
                logging.info("Successfully incremented qty in balance collection.")
            else:
                logging.info("Failed updating record in balance collection.")

        else:
            # Create new record in balance collection
            obj = {
                'product_id': product_id,
                'location_id': to_location,
                'qty': quantity
            }

            res = requests.post(url=BALANCE_SERVICE_URL, json=obj)
            if res.status_code == 201:
                logging.info("Successfully created record in balance collection.")
            else:
                logging.info("Failed creating record in balance collection.")

    # Product moving out of a location
    if from_location and not to_location:
        if product_exists_at_location(product_id, from_location):
            from_location_current_qty = get_product_qty(product_id, from_location)

            if from_location_current_qty >= quantity:
                # Decrement quantity
                final_qty = from_location_current_qty - quantity
                post_obj = {
                    'product_id': product_id,
                    'location_id': from_location,
                    'qty': final_qty
                }

                res = requests.put(url=BALANCE_SERVICE_URL, json=post_obj)
                if res.status_code == 201:
                    logging.info("Successfully decremented qty in balance collection.")
                else:
                    logging.info("Failed updating record in balance collection.")

            else:
                logging.info("Outgoing movement quantity cannot be greater than existing quantity.")

        else:
            logging.info("Product not found at given location.")

    # Product being moved between two locations
    if from_location and to_location:
        if product_exists_at_location(product_id, from_location):
            from_location_current_qty = get_product_qty(product_id, from_location)

            if from_location_current_qty >= quantity:
                from_location_final_qty = from_location_current_qty - quantity

                # Decrement qty in from_location
                decrement_obj = {
                    'product_id': product_id,
                    'location_id': from_location,
                    'qty': from_location_final_qty
                }
                decrement_res = requests.put(url=BALANCE_SERVICE_URL, json=decrement_obj)

                if decrement_res.status_code == 201:
                    logging.info("successfully decremented qty at from_location")

                    if product_exists_at_location(product_id, to_location):
                        to_location_current_qty = get_product_qty(product_id, to_location)
                        to_location_final_qty = to_location_current_qty + quantity

                        increment_obj = {
                            'product_id': product_id,
                            'location_id': from_location,
                            'qty': to_location_final_qty
                        }
                        increment_res = requests.put(url=BALANCE_SERVICE_URL, json=increment_obj)

                        if increment_res.status_code == 201:
                            logging.info("Successfully incremented qty at to_location")

                        else:
                            logging.info("Failed incrementing qty at to_location")

                    else:
                        increment_obj = {
                            'product_id': product_id,
                            'location_id': from_location,
                            'qty': quantity
                        }
                        increment_res = requests.post(url=BALANCE_SERVICE_URL, json=increment_obj)

                        if increment_res.status_code == 201:
                            logging.info("Successfully created record in balance collection")

                        else:
                            logging.info("Failed creating record in balance collection")

                else:
                    logging.info(
                        "Failed decrementing qty at from_location. qty at to_location will not be incremented.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    time.sleep(10)  # Temporary fix to solve connection issue on running docker-compose up
    main()
