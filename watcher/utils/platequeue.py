import time
import datetime
from collections import deque

from watcher.models.plateinfo import plateInfo
from watcher.utils.db import MongoDBManager
from config import CONFIG



class plateQueue:
    def __init__(self, keep_time: float = 600.0):
        self.keep_time = keep_time
        self.queue = deque()
        self.plate_set = set()
        self.db_manager = MongoDBManager()
        self.plates_collection = self.db_manager.get_collection(CONFIG.database.all_plates)
  

    def _purge_expired(self):
        current_time = time.monotonic()
        while self.queue and (current_time - self.queue[0][0]) > self.keep_time:
            _,plate = self.queue.popleft()
            plate.endtimestamp = plate.starttimestamp + 10.00
            plate.timestamp =  datetime.datetime.now()
            self.db_manager.log_fueling(CONFIG.database.all_plates, plate)
            print(plate.plate + "added to log")
            self.plate_set.discard(plate.plate)

    def add(self, plateinfo: plateInfo):
        self._purge_expired()
        now = time.monotonic()
        if plateinfo.plate in self.plate_set:
            return 
        plateinfo.starttimestamp = plateinfo.timestamp
        self.queue.append((now, plateinfo))
        self.plate_set.add(plateinfo.plate)

    def contains(self,plate):
        self._purge_expired()
        return plate in self.plate_set

    def get_all(self):
        self._purge_expired()
        return [plateinfo for _, plateinfo in self.queue]

    def __len__(self):
        self._purge_expired()
        return len(self.queue)
