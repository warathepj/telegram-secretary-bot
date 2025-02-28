import pymongo
from bson import ObjectId

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["restaurant"]
menus_collection = db["menus"]

# Fetch all menu items
all_menus = list(menus_collection.find())

# Print menu items
for menu in all_menus:
    print(f"Name (TH): {menu['name']}")
    print(f"Name (EN): {menu['nameE']}")
    print(f"Price: {menu['price']} THB")
    print(f"Recommended: {menu['recommend']}")
    print("-" * 50)

# Example: Fetch a specific menu item by ID
specific_menu = menus_collection.find_one({"_id": ObjectId("67c02879375bf91ada24feea")})
if specific_menu:
    print("\nSpecific menu item:")
    print(f"Name (TH): {specific_menu['name']}")
    print(f"Name (EN): {specific_menu['nameE']}")
    print(f"Price: {specific_menu['price']} THB")

# Close the connection
client.close()
