# PersonaRise – Resume Analyzer

PersonaRise is a resume analysis tool that extracts skills, education, experience, and key information using Flask and Google Cloud APIs.

## Features
- Resume text extraction (PDF/Text)
- Skill and entity extraction using Google Natural Language API
- User registration and login
- SQLite database support
- Flask backend with API routes

## APIs Used
### Google Cloud Natural Language API
Used for analyzing resume text and extracting entities.

Store the key in a `.env` file:

GOOGLE_API_KEY=your_api_key


Load it in `app.py`:
```python
from dotenv import load_dotenv
import os
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
```

## Project Structure

app.py
requirements.txt
users.db
.env (not pushed to GitHub)
data/


## How to Run
Install dependencies:

pip install -r requirements.txt
Create `.env` with your API key.

Run the server:
python app.py


Open in browser:
http://127.0.0.1:5000/


## API Endpoints
- POST /upload – Analyze resume
- POST /register – Register user
- POST /login – Login
- GET /users – Get users list

## Developer
Rachana D N
