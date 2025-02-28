import pymongo
from bson import ObjectId
import google.generativeai as genai
import pandas as pd
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class MongoDBLLMAnalyzer:
    def __init__(self, connection_string: str, db_name: str):
        try:
            self.client = pymongo.MongoClient(connection_string)
            self.client.admin.command("ping")
            logging.info(f"Connected to MongoDB successfully")

            self.db = self.client[db_name]
            self.model = genai.GenerativeModel("gemini-2.0-flash")

            collections = self.db.list_collection_names()
            logging.info(f"Available collections: {collections}")
        except Exception as e:
            logging.error(f"Failed to initialize MongoDB connection: {str(e)}")
            raise

    def get_collection_info(self, collection_name: str) -> dict:
        try:
            collection = self.db[collection_name]
            doc_count = collection.count_documents({})

            sample = None
            if doc_count > 0:
                sample = collection.find_one()

            return {
                "exists": True,
                "document_count": doc_count,
                "sample_keys": list(sample.keys()) if sample else None,
            }
        except Exception as e:
            logging.error(
                f"Error getting collection info for '{collection_name}': {str(e)}"
            )
            return {"exists": False, "error": str(e)}

    def _convert_dates_to_str(self, doc: Dict) -> Dict:
        """Helper method to convert dates to strings"""
        converted = {}
        for key, value in doc.items():
            if isinstance(value, dict):
                converted[key] = self._convert_dates_to_str(value)
            elif isinstance(value, (list, tuple)):
                converted[key] = [
                    self._convert_dates_to_str(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                converted[key] = str(value) if hasattr(value, "strftime") else value
        return converted

    def analyze_collection_with_llm(
        self, collection_name: str, question: str, context: str = ""
    ) -> str:
        try:
            collection_info = self.get_collection_info(collection_name)
            if not collection_info["exists"]:
                return f"Collection '{collection_name}' does not exist."

            logging.info(
                f"Analyzing collection '{collection_name}' with {collection_info['document_count']} documents"
            )
            logging.info(f"User question: {question}")

            collection = self.db[collection_name]
            all_docs = list(collection.find())

            if not all_docs:
                return f"The collection '{collection_name}' is empty."

            simplified_docs = []
            for doc in all_docs:
                if "_id" in doc and isinstance(doc["_id"], ObjectId):
                    doc["_id"] = str(doc["_id"])
                doc_copy = self._convert_dates_to_str(doc)
                simplified_docs.append(doc_copy)

            json_data = json.dumps(simplified_docs, ensure_ascii=False, indent=2)

            # Detect if question is in English (you can add more sophisticated language detection if needed)
            is_english = not any(
                "\u0E00" <= c <= "\u0E7F" for c in question
            )  # Simple Thai character range check

            if collection_name == "about":
                prompt_template = """
                You are a restaurant chat assistant. Answer questions about the restaurant information concisely.
                
                The restaurant information is stored in the "about" collection:
                {json_data}
                
                Previous conversation context:
                {context}
                
                Question about the restaurant: {question}
                
                Important instructions:
                1. Answer directly and concisely in less than 50 words
                2. If the question is in Thai, answer in Thai. If the question is in English, answer in English
                3. Only mention relevant information that directly answers the question
                4. Consider the conversation context when appropriate
                5. You MUST respond in English for English questions
                """
            else:
                prompt_template = """
                You are a restaurant chat assistant. Answer questions about the menu items concisely.
                
                The menu information is stored in the "{collection_name}" collection:
                {json_data}
                
                Previous conversation context:
                {context}
                
                Question about the menu: {question}
                
                Important instructions:
                1. Answer directly and concisely in less than 50 words
                2. If the question is in Thai, answer in Thai. If the question is in English, answer in English
                3. Only mention menu items that directly answer the question
                4. Consider the conversation context when appropriate
                5. You MUST respond in English for English questions
                """

            prompt = prompt_template.format(
                json_data=json_data,
                question=question,
                collection_name=collection_name,
                context=context,
            )

            response = self.model.generate_content(
                prompt,
                generation_config={"temperature": 0.2, "max_output_tokens": 150},
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                    },
                ],
            )

            return response.text

        except Exception as e:
            error_msg = f"Error analyzing collection: {str(e)}"
            logging.error(error_msg)
            return error_msg

    def close_connection(self):
        self.client.close()
        logging.info("MongoDB connection closed")


# Example usage
if __name__ == "__main__":
    # Initialize analyzer
    analyzer = MongoDBLLMAnalyzer(
        connection_string="mongodb://localhost:27017/", db_name="restaurant"
    )

    # Analyze collection
    response = analyzer.analyze_collection_with_llm(
        collection_name="menus", question="What are the menus?"
    )
    print("LLM Analysis:", response)

    # Get query suggestions
    query_suggestions = analyzer.get_query_suggestions("menus")
    print("\nQuery Suggestions:", query_suggestions)

    # Get visualization recommendations
    viz_recommendations = analyzer.recommend_visualizations("menus")
    print("\nVisualization Recommendations:", viz_recommendations)

    # Close connection
    analyzer.close_connection()
