# Telegram AI Secretary Bot

A FastAPI-powered Telegram bot that acts as an AI secretary, helping you manage tasks, notes, and conversations using Google's Gemini AI model.

## 🌟 Features

- 🤖 Powered by Google's Gemini AI model for natural language understanding
- 📱 Seamless Telegram integration
- 📝 Task and note management
- ⏰ Smart time parsing for tasks
- 💬 Bilingual support (English/Thai)
- 🔍 Context-aware conversations
- 🔒 Built-in safety settings
- 💾 MongoDB for data persistence
- 🎨 Retro-style web dashboard

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.7+
- **Database**: MongoDB
- **AI Model**: Google Gemini
- **Bot Framework**: python-telegram-bot
- **Frontend**: HTML, CSS, JavaScript
- **Documentation**: Swagger UI, ReDoc

## 📋 Prerequisites

- Python 3.7+
- MongoDB
- Google Gemini API key
- Telegram Bot Token

## 🚀 Installation

1. Clone the repository:

```bash
git clone https://github.com/warathepj/telegram-secretary-bot.git
cd telegram-secretary-bot
```

2. Create and activate virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:

```bash
GEMINI_API_KEY=your_api_key_here
TELEGRAM_BOT_TOKEN=your_bot_token_here
ALLOWED_CHAT_IDS=123456789,987654321
```

## 🤖 Bot Commands

- `/start` - Start the bot
- `/help` - Show help message
- `/mychatid` - Get your chat ID
- `/task` - Add a new task with time
- `/note` - Save a quick note

### Task Examples

```
/task Buy groceries at 14:30
/task Meeting tomorrow at 10am
/task Dentist appointment next monday 15:00
```

### Note Example

```
/note Remember to call John
```

## 🏃‍♂️ Running the Application

1. Start the server:

```bash
uvicorn main:app --reload
```

2. Access the interfaces:

- Web Dashboard: http://localhost:8000
- ReDoc: http://localhost:8000/redoc

## 📚 API Endpoints

### Telegram Data Endpoint

```http
GET /telegram-data
```

### Bot Status Endpoint

```http
GET /bot/status
```

## 💾 Database Collections

- **data**: Stores tasks, notes, and conversation data
- **users**: User preferences and settings

## 🔒 Security Features

- Authorized chat IDs only
- Content filtering with safety settings
- API key authentication
- Input validation
- Rate limiting capabilities

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

TODO:

////////////
//////////
