# mongodb.py
from pymongo import MongoClient
from django.conf import settings

client = MongoClient(settings.MONGO_URI)
db = client['pushup_counter']

users_collection = db['users']
profiles_collection = db['profiles']