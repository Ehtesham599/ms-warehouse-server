import pymongo
from decouple import config

client = pymongo.MongoClient(config("DB_CONNECTION_STRING"))
db = client["balance"]
collection = db["balance"]
