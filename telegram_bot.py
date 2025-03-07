import os
import logging
from datetime import datetime
import re
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from llm import MongoDBLLMAnalyzer

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get token and allowed chat IDs from environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN provided in .env file")

ALLOWED_CHAT_IDS = os.getenv("ALLOWED_CHAT_IDS", "").split(",")
ALLOWED_CHAT_IDS = [
    int(chat_id.strip()) for chat_id in ALLOWED_CHAT_IDS if chat_id.strip()
]

# Initialize the LLM analyzer
try:
    analyzer = MongoDBLLMAnalyzer(
        connection_string="mongodb://localhost:27017/", db_name="telegram-secretary-bot"
    )
    logger.info("MongoDB LLM Analyzer initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize MongoDB LLM Analyzer: {str(e)}")
    raise


# Command handler for /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    try:
        chat_id = update.effective_chat.id
        if not ALLOWED_CHAT_IDS or chat_id in ALLOWED_CHAT_IDS:
            await update.message.reply_text(
                "Hello! I'm your secretary bot. How can I help you today?"
            )
        else:
            await update.message.reply_text(
                "Sorry, you're not authorized to use this bot."
            )
            logger.warning(f"Unauthorized access attempt from chat ID: {chat_id}")
    except Exception as e:
        logger.error(f"Error in start_command: {str(e)}")


# Message handler for text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process messages using LLM."""
    try:
        chat_id = update.effective_chat.id
        if not ALLOWED_CHAT_IDS or chat_id in ALLOWED_CHAT_IDS:
            text = update.message.text

            # Get chat context from user data
            if not context.user_data.get("chat_history"):
                context.user_data["chat_history"] = []

            # Add user message to history
            context.user_data["chat_history"].append(f"User: {text}")

            # Keep only last 10 messages for context
            chat_history = context.user_data["chat_history"][-10:]
            context_str = "\n".join(chat_history)

            # Get response from LLM
            response = analyzer.analyze_collection_with_llm(
                collection_name="data", question=text, context=context_str
            )

            # Add bot response to history
            context.user_data["chat_history"].append(f"Assistant: {response}")

            await update.message.reply_text(response)
            logger.info(f"Message from {chat_id}: {text}")
            logger.info(f"Response: {response}")
    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}")
        await update.message.reply_text(
            "Sorry, I encountered an error processing your request."
        )


# Helper command to get your chat ID
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the chat ID of the user."""
    try:
        chat_id = update.effective_chat.id
        await update.message.reply_text(f"Your chat ID is: {chat_id}")
        logger.info(f"Chat ID request from: {chat_id}")
    except Exception as e:
        logger.error(f"Error in get_chat_id: {str(e)}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.error(f"Update {update} caused error {context.error}")


async def note_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save a note when the command /note is issued."""
    try:
        chat_id = update.effective_chat.id
        if not ALLOWED_CHAT_IDS or chat_id in ALLOWED_CHAT_IDS:
            # Get the text after "/note "
            note_text = update.message.text[6:].strip()

            if note_text:
                # Create note document
                note_doc = {"description": note_text, "type": "note"}

                # Save to MongoDB
                data_collection = analyzer.db["data"]
                data_collection.insert_one(note_doc)

                # Store in user_data and log
                context.user_data["note"] = note_text
                logger.info(f"Note from chat ID {chat_id}: {note_text}")
                await update.message.reply_text(f"Note saved: {note_text}")
            else:
                await update.message.reply_text("Please provide some text after /note")

        else:
            await update.message.reply_text(
                "Sorry, you're not authorized to use this bot."
            )
            logger.warning(f"Unauthorized access attempt from chat ID: {chat_id}")
    except Exception as e:
        logger.error(f"Error in note_command: {str(e)}")


async def task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save a task when the command /task is issued."""
    try:
        chat_id = update.effective_chat.id
        if not ALLOWED_CHAT_IDS or chat_id in ALLOWED_CHAT_IDS:
            # Get the text after "/task "
            task_text = update.message.text[6:].strip()

            if task_text:
                # Get current date
                today = datetime.now().strftime("%Y-%m-%d")

                # Get response from LLM to parse time
                prompt = f"""You are a task parser. Parse this Thai task with time: "{task_text}"
Today's date is: {today}
Return ONLY a valid JSON object in this exact format, nothing else:
{{
    "description": "task description without time",
    "time": "YYYY-MM-DD HH:mm",
    "has_explicit_date": boolean
}}
Rules:
- If no specific date is mentioned in the task, use today's date ({today}) and set has_explicit_date to false
- If a specific date is mentioned, parse that date and set has_explicit_date to true
- Always convert Thai time words to 24-hour format
- Time must be in HH:mm format"""

                response = analyzer.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0,
                        "candidate_count": 1,
                    },
                )

                try:
                    # Clean the response text by removing markdown code block
                    cleaned_response = response.text.strip()
                    if cleaned_response.startswith("```"):
                        cleaned_response = cleaned_response.split("\n", 1)[1]
                    if cleaned_response.endswith("```"):
                        cleaned_response = cleaned_response.rsplit("\n", 1)[0]
                    cleaned_response = cleaned_response.strip()
                    if cleaned_response.startswith("json"):
                        cleaned_response = cleaned_response[4:].strip()

                    parsed = json.loads(cleaned_response)
                    # Validate required fields
                    if not all(
                        key in parsed
                        for key in ["description", "time", "has_explicit_date"]
                    ):
                        raise ValueError("Missing required fields in response")

                    # If no explicit date was mentioned, ensure we're using today's date
                    if not parsed["has_explicit_date"]:
                        time_part = parsed["time"].split(" ")[1]
                        parsed["time"] = f"{today} {time_part}"

                    # Create task document
                    task_doc = {
                        "description": parsed["description"],
                        "type": "task",
                        "time": parsed["time"],
                    }

                    # Save to MongoDB
                    data_collection = analyzer.db["data"]
                    data_collection.insert_one(task_doc)

                    # Store in user_data and log
                    context.user_data["task"] = task_text
                    logger.info(f"Task from chat ID {chat_id}: {task_text}")
                    await update.message.reply_text(
                        f"Task saved: {parsed['description']} at {parsed['time']}"
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM response: {response.text}")
                    await update.message.reply_text(
                        "Sorry, I couldn't understand the time format. Please try again."
                    )
            else:
                await update.message.reply_text(
                    "Please provide task details after /task"
                )
        else:
            await update.message.reply_text(
                "Sorry, you're not authorized to use this bot."
            )
            logger.warning(f"Unauthorized access attempt from chat ID: {chat_id}")
    except Exception as e:
        logger.error(f"Error in task_command: {str(e)}")
        await update.message.reply_text(
            "Sorry, I encountered an error processing your request."
        )


def main() -> None:
    """Start the bot."""
    try:
        # Create application
        application = Application.builder().token(TOKEN).build()

        # Add command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("mychatid", get_chat_id))
        application.add_handler(CommandHandler("note", note_command))
        application.add_handler(CommandHandler("task", task_command))  # Add this line

        # Add message handler
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        )

        # Add error handler
        application.add_error_handler(error_handler)

        # Start the bot
        logger.info("Starting bot...")
        logger.info(f"Allowed chat IDs: {ALLOWED_CHAT_IDS or 'All (no restrictions)'}")

        # Start the bot with polling
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        # Close MongoDB connection when bot stops
        analyzer.close_connection()


if __name__ == "__main__":
    main()
