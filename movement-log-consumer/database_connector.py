import pymongo
from decouple import config

client = pymongo.MongoClient(config("DB_CONNECTION_STRING"))
balance_db = client["balance"]
balance_collection = balance_db["balance"]
