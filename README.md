# Restaurant Chat Assistant

A FastAPI-based chat assistant that provides information about restaurant menus and details using Google's Gemini AI model.

## Features

- 🤖 Powered by Google's Gemini AI model
- 🌐 RESTful API using FastAPI
- 💬 Bilingual support (English/Thai)
- 🍽️ Restaurant information and menu queries
- 📝 Context-aware conversations
- 🔒 Built-in safety settings

## Prerequisites

- Python 3.7+
- MongoDB
- Google AI API key

## Installation

1. Clone the repository:

```bash
git clone [your-repository-url]
cd [repository-name]
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
# Create .env file with:
GOOGLE_API_KEY=your_api_key_here
MONGODB_URI=your_mongodb_uri
```

## Usage

1. Start the server:

```bash
uvicorn main:app --reload
```

2. Access the API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Chat Endpoint

```http
POST /chat
```

Request body:

```json
{
  "question": "What's on the menu?",
  "context": "Previous conversation context (optional)"
}
```

Response:

```json
{
  "answer": "Response from the assistant"
}
```

## Database Collections

### About Collection

Stores restaurant information:

- Name
- Location
- Contact details
- Operating hours

### Menu Collection

Stores menu items:

- Name
- Description
- Price
- Category
- Availability

## Development

- The project uses FastAPI for the web framework
- MongoDB for data storage
- Google's Generative AI (Gemini) for natural language processing
- Supports both English and Thai languages

## Security

- Implements safety settings for content filtering
- API key authentication
- Input validation
- Rate limiting (if configured)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your chosen license]

## Contact

[Your contact information]
