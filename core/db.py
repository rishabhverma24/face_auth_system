import json
import os
import datetime
from typing import List, Dict, Optional

DB_FILE = "data.json"

class Database:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self):
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w') as f:
                json.dump({"users": [], "history": []}, f, indent=4)

    def _load(self) -> Dict:
        with open(self.db_path, 'r') as f:
            return json.load(f)

    def _save(self, data: Dict):
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=4)

    def add_user(self, name: str, encoding: List) -> int:
        """
        Registers a new user and returns their INT ID.
        """
        data = self._load()
        
        # New Strategy: IDs are Integers 1, 2, 3...
        # Find max id
        existing_ids = [int(u["id"]) for u in data["users"]]
        if existing_ids:
            new_id = max(existing_ids) + 1
        else:
            new_id = 1
            
        new_user = {
            "id": new_id, # Stored as int
            "name": name,
            "encoding": encoding, # Placeholder in LBPH mode
            "created_at": str(datetime.datetime.now())
        }
        data["users"].append(new_user)
        self._save(data)
        return new_id

    def get_users(self) -> List[Dict]:
        return self._load()["users"]

    def log_attendance(self, user_id: str, user_name: str, event_type: str) -> bool:
        data = self._load()
        now = datetime.datetime.now()
        
        # Debounce
        user_logs = [log for log in data["history"] if str(log["user_id"]) == str(user_id)]
        if user_logs:
            last_log = user_logs[-1]
            last_time = datetime.datetime.fromisoformat(last_log["timestamp"])
            if (now - last_time).total_seconds() < 60: 
                return False

        new_log = {
            "user_id": str(user_id),
            "name": user_name,
            "type": event_type, 
            "timestamp": str(now)
        }
        data["history"].append(new_log)
        self._save(data)
        return True

    def get_history(self) -> List[Dict]:
        return self._load()["history"]
