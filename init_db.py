import pymongo
from datetime import datetime

def init_about_collection():
    # Connect to MongoDB
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["restaurant"]
    about_collection = db["about"]

    # Clear existing data
    about_collection.delete_many({})

    # Restaurant information
    about_data = {
        "name": {
            "th": "ไทยแท้",
            "en": "Thai Tae"
        },
        "founded_year": 2525,
        "founder": {
            "th": "สมชาย",
            "en": "Somchai"
        },
        "history": {
            "establishment": {
                "th": "ก่อตั้งขึ้นในปี พ.ศ. 2525 โดยคุณสมชาย ผู้มีใจรักในอาหารไทย",
                "en": "Founded in 1982 by Somchai, who has a passion for Thai cuisine"
            },
            "mission": {
                "th": "นำเสนอรสชาติอาหารไทยแท้ๆ และรักษาเอกลักษณ์ของอาหารไทย",
                "en": "To present authentic Thai flavors and preserve the uniqueness of Thai cuisine"
            },
            "philosophy": {
                "th": "พิถีพิถันในการคัดสรรวัตถุดิบคุณภาพและปรุงอาหารด้วยสูตรต้นตำรับ",
                "en": "Meticulous selection of quality ingredients and cooking with original recipes"
            }
        },
        "unique_features": {
            "cuisine_types": {
                "th": ["อาหารไทยภาคกลาง", "ภาคเหนือ", "ภาคอีสาน", "ภาคใต้"],
                "en": ["Central Thai Cuisine", "Northern Thai Cuisine", "Northeastern Thai Cuisine", "Southern Thai Cuisine"]
            },
            "atmosphere": {
                "th": "อบอุ่นและเป็นกันเอง สะท้อนวัฒนธรรมไทย",
                "en": "Warm and friendly atmosphere, reflecting Thai culture"
            },
            "service": {
                "th": "บริการที่อบอุ่นเป็นกันเอง",
                "en": "Warm and friendly service"
            }
        },
        "achievements": {
            "awards": {
                "th": ["อันดับ 1 The World's 50 Best Restaurants"],
                "en": ["Number 1 in The World's 50 Best Restaurants"]
            },
            "recognition": {
                "th": "ได้รับการตอบรับที่ดีจากลูกค้าทั้งชาวไทยและชาวต่างชาติ",
                "en": "Well received by both Thai and international customers"
            }
        },
        "last_updated": datetime.now()
    }

    # Insert data
    about_collection.insert_one(about_data)
    print("About collection initialized successfully")

if __name__ == "__main__":
    init_about_collection()