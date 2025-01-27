from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from AI_managers_sales_toys.work_with_database_MongoDB.config import PASSWORD_MONGODB, LOGIN_MONGODB


uri = f"mongodb+srv://{LOGIN_MONGODB}:{PASSWORD_MONGODB}@cluster0.o7x8l.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))


class Messages:
    def __init__(self,db_name, collection_name):
        global client
        mongodb_client = client
        self.db = mongodb_client[db_name]
        self.collection = self.db[collection_name]

    def add_message_to_inst_db(self, username, user_id_inst, messenger_name, role, content):
        message = {'user_id': user_id_inst , 'username': username, 'messenger_name': messenger_name, 'role': role, 'content': content}
        self.collection.insert_one(message)

    def add_message_to_tg_db(self, username, user_id_tg, messenger_name, role, content):
        message = {'username': username, 'user_id_tg': user_id_tg, 'messenger_name': messenger_name, 'role': role, 'content': content}
        self.collection.insert_one(message)

    def add_thread_id(self, username, thread_id):
        self.collection.insert_one({'_id': username, 'thread_id': thread_id})

    def search_tread_id(self, contact_id):
        return self.collection.find_one({'_id': contact_id}, {'thread_id': 1})