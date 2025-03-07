import pymongo
from bson import ObjectId
from datetime import datetime


def fetch_formatted_data():
    # Connect to MongoDB
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["telegram-secretary-bot"]
    data_collection = db["data"]

    try:
        # Fetch all data
        all_data = list(data_collection.find())

        # Format the data
        formatted_data = []
        for item in all_data:
            formatted_item = {}
            for key, value in item.items():
                if isinstance(value, ObjectId):
                    formatted_item[key] = str(value)
                elif isinstance(value, datetime):
                    formatted_item[key] = value.isoformat()
                else:
                    formatted_item[key] = value
            formatted_data.append(formatted_item)

        return formatted_data
    finally:
        client.close()


if __name__ == "__main__":
    data = fetch_formatted_data()
    for item in data:
        print(f"Description: {item.get('description')}")
        print(f"Type: {item.get('type')}")
        print("-" * 50)
