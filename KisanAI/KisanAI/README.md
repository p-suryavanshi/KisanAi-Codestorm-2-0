# 🌾 KisanAI — AI Farmer Advisory Platform
> PS3 Hackathon Submission · FastAPI + OpenAI + Python

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env        # add your OPENAI_API_KEY (optional)
uvicorn main:app --reload --port 8000
```
Open http://localhost:8000

## Project Structure
```
kisanai/
├── main.py              ← FastAPI backend
├── requirements.txt
├── .env.example
├── templates/index.html ← Jinja2 template
└── static/
    ├── style.css
    └── app.js
```

## API Routes
POST /api/chat          ← AI crop advisory
POST /api/pest-detect   ← Pest image analysis
GET  /api/weather/{state}
GET  /api/market
GET  /api/health

## Works without API key in Demo Mode!
