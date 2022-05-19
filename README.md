# Microservice Warehouse Server
> A fully distributed RESTful warehouse server following a microservice architecture.

## Introduction
This project was developed with the intention to learn technologies such as the microservice architecture, RESTful APIs, MongoDB (NoSQL database), message queueing using RabbitMQ and docker compose.\
A warehouse management application provides the perfect use case to implement above-mentioned technologies at scale.

The system uses the following tech stack:
- Server side: Flask RESTful (Python)
- Database: [MongoDB Atlas](https://www.mongodb.com/docs/atlas/)
- Message Queueing: [RabbitMQ](https://www.rabbitmq.com/)
- Deployment: [Docker](https://www.docker.com/)

## Design
![architecture](https://user-images.githubusercontent.com/45887110/169351624-cdfd4dcd-6fdd-45b3-9b75-530e3fba2117.jpg)


The system consists of four client facing RESTful services: `balance-service`, `product-service`, `location-service`, `movement-service`.

When making a POST request to the `movement-service` (`localhost:8003`), i.e. creating a new movement of a product, request body is published to the  `movement_log` queue.
Upon publishing the message, the `movement-log-consumer` service consumes this message, parses through the request body and allocates the product into the balance database by making RESTful calls to the `balance-service`.

## Resources

### Product Resource
External URL: `localhost:8001`
#### View Products
A `GET` request can be made to the given URL to view the list of products.

#### Add a product
A `POST` request can be made to the given URL to add a new product in the database.\
The required fields in the request JSON body are `product_name` and `product_description`.

The post body must look something like below:
```
{
    "product_name": "YOUR PRODUCT NAME",
    "product_description": "YOUR PRODUCT DESCRIPTION",
    .
    .
    .
}
```

### Location Resource
External URL: `localhost:8002`
#### View Locations
A `GET` request can be made to the given URL to view the list of warehouse locations.

#### Add Locations
A `POST` request can be made to the given URL to add a new location in the database.\
The required fields in the request JSON body are `location_name`, `location_latitude` and `location_longitude`.

The post body must look something like below:
```
{
    "location_name": "YOUR LOCATION NAME",
    "location_latitude": "YOUR LOCATION LATITUDE",
    "location_longitude": "YOUR LOCATION LONGITUDE",
    .
    .
}
```

### Movement Resource
External URL: `localhost:8003`
#### View product movements
A `GET` request can be made to the given URL to view the list of product movements between locations.

#### Add movement
A `POST` request can be made to the given URL to add a new product movement.\
The required fields in the request JSON body are `from_location`, `to_location`, `product_id` and `qunatity`,
where `from_location` and `to_location` are location IDs that are generated once locations have been added to the database and can be obtained while viewing locations,
and likewise for `product_id`. The `quantity` value must be of type integer and greater than 0.

The post body must look something like below:
```
{
    "from_location": "LOCATION_ID",
    "to_location": "LOCATION_ID",
    "product_id": "PRODUCT_ID",
    "quantity": "QUANTITY<int>"
}
```

Note: If the product is being added to a location, the `from_location` can be empty.
If the product is being moved out of a location, `to_location` can be empty.
If the product is being moved between locations, both `from_location` and `to_location` must be provided.

### Balance Resource
External URL: `localhost:8000`
#### View product balance
Product balance in respective warehouses can be viewed by making a `GET` request to the given URL.
