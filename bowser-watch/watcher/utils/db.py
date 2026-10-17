class MongoDBManager:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="bowser_watch"):
        from pymongo import MongoClient
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def add_to_watchlist(self, plate, amount):
        watchlist_collection = self.db['watchlist']
        watchlist_collection.insert_one({"plate": plate, "amount": amount})

    def get_watchlist(self):
        watchlist_collection = self.db['watchlist']
        return list(watchlist_collection.find())

    def close(self):
        self.client.close()