import pymongo
from decouple import config

client = pymongo.MongoClient(config("DB_CONNECTION_STRING"))
db = client["locations"]
collection = db["locations"]
