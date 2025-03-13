import pymongo
from bson import ObjectId
from datetime import datetime
from typing import List, Dict, Any, Union
import json

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

def fetch_formatted_data(collection_name: str = "data") -> List[Dict[str, Any]]:
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["telegram-secretary-bot"]
    collection = db[collection_name]

    try:
        # Fetch all data
        all_data = list(collection.find())

        # Format the data
        formatted_data = []
        for item in all_data:
            formatted_item = {}
            for key, value in item.items():
                if isinstance(value, ObjectId):
                    formatted_item[key] = str(value)
                elif isinstance(value, datetime):
                    formatted_item[key] = value.isoformat()
                elif isinstance(value, (dict, list)):
                    # Handle nested structures
                    formatted_item[key] = json.loads(
                        json.dumps(value, cls=JSONEncoder)
                    )
                else:
                    formatted_item[key] = value
            formatted_data.append(formatted_item)

        return formatted_data
    finally:
        client.close()

def get_all_collections() -> List[str]:
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["telegram-secretary-bot"]
    try:
        return db.list_collection_names()
    finally:
        client.close()


if __name__ == "__main__":
    data = fetch_formatted_data()
    for item in data:
        print(f"Description: {item.get('description')}")
        print(f"Type: {item.get('type')}")
        print("-" * 50)
