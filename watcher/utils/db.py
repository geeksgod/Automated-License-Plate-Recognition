import os
import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import CONFIG
from watcher.models.plateinfo import plateInfo
import datetime 

class MongoDBManager:
    _instance = None
    _client = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, uri: str = None, db_name: str = None):
        # Use provided credentials or fall back to environment variables
        self.uri = uri or os.getenv("MONGO_URI", CONFIG.database.conection_string)
        self.db_name = db_name or os.getenv("MONGO_DB_NAME", CONFIG.database.db_name)
        self.connected = True

        if not MongoDBManager._client:
            try:
                tlsCAFile=certifi.where()
                # MongoClient manages its own internal connection pool automatically
                MongoDBManager._client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
                # Force a connection call to validate credentials/network instantly
                MongoDBManager._client.admin.command('ping')
                self.connected = True
                print("Successfully connected to MongoDB.")
                
            except ConnectionFailure as e:
                print(f"Could not connect to MongoDB: {e}")
                MongoDBManager._client = None
                raise

        self.db = MongoDBManager._client[self.db_name]

    def get_collection(self, collection_name: str):
        """Helper to quickly grab a specific collection."""
        return self.db[collection_name]

    def close(self):
        """Closes the connection pool entirely."""
        if MongoDBManager._client:
            MongoDBManager._client.close()
            MongoDBManager._client = None
            print("MongoDB connection closed.")

    def add_to_watchlist(self, plate: str, amount: str):
            record = {
                "plate": plate.strip().upper(),
                "amount": amount.strip() or "Unspecified",
                "date_added": datetime.datetime.now().strftime("%Y-%m-%d"),
            }
            if self.connected:
                try:
                    self.get_collection(CONFIG.database.watch_list).update_one({ "plate": record["plate"] },{ "$set": record},upsert = True)
                    return True
                except Exception:
                    self.connected = False
            return True

    def delete_from_watchlist(self, plate):
        plate_to_delete = plate.strip().upper()

        if self.connected:
            try:
                result = self.get_collection(CONFIG.database.watch_list).delete_one(
                    {"plate": plate_to_delete}
                )
                if result.deleted_count > 0:
                    print(f"Successfully deleted plate: {plate_to_delete}")
                    return True
                else:
                    print(f"plate {plate_to_delete} not found in the watchlist.")
                    return False
                    
            except Exception as e:
                print(f"MongoDB Delete Failed: {e}")
                self.connected = False

        return False


    def get_watchlist(self,collection):
                if self.connected:
                    try:
                        # start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                        # cursor = self.get_collection(collection_name=collection).find({"timestamp": {"$gte": start}}).sort("timestamp", -1)
                        cursor = self.get_collection(collection_name=collection).find()
                        return list(cursor)
                    except Exception:
                        self.connected = False
    
    
    def check_watchlist(self, plate: str):       
        if not plate:
            return None

        return self.get_collection(CONFIG.database.watch_list).find_one(
            {"plate": plate},
            {"_id": 0}  
        )
    
    def log_fueling(self, collection, info: plateInfo ):
            if self.connected:
                try:
                    self.get_collection(collection_name=collection).update_one({ "plate": info.plate },{ "$set": info.__dict__},upsert = True)
                    return True
                except Exception:
                    self.connected = False
            return True
    
    def get_todays_logs(self,collection):
            if self.connected:
                try:
                    # start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    # cursor = self.get_collection(collection_name=collection).find({"timestamp": {"$gte": start}}).sort("timestamp", -1)
                    cursor = self.get_collection(collection_name=collection).find()
                    return list(cursor)
                except Exception:
                    self.connected = False
