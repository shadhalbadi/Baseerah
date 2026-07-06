# Baseerah — بصيرة

**AI-powered utility bill intelligence for water & electricity.**

Baseerah turns raw water and electricity bills into actionable insight: it detects unusual
consumption, flags probable leaks and inefficiencies, forecasts upcoming cost, and delivers
personalized savings recommendations — aligned with Oman Vision 2040 sustainability goals.

> *Baseerah* (بصيرة) is Arabic for **insight / discernment**.

## Features

- 📄 **Bill upload & OCR** — extract consumption, cost, and billing dates from image and PDF
  utility bills (bilingual Arabic/English), powered by Tesseract with Claude-assisted parsing.
- 📈 **Anomaly detection** — spot unusual spikes against the user's own history.
- 💧 **Leak & inefficiency flags** — surface likely waste (e.g. continuous overnight flow).
- 💡 **Savings recommendations** — prioritized by estimated savings and effort.

## Tech Stack

| Layer      | Stack                                                        |
|------------|--------------------------------------------------------------|
| Frontend   | React 19 + TypeScript, Vite, Tailwind CSS, i18next (AR/EN)   |
| Backend    | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic                   |
| Auth       | JWT (PyJWT)                                                  |
| OCR / AI   | pytesseract + Pillow + pypdf, Anthropic Claude SDK           |
| Database   | SQLite (dev)                                                 |

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) binary (OCR self-disables if missing)

### Backend

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in values (e.g. BASEERAH_ANTHROPIC_API_KEY)
alembic upgrade head
python seed.py              # optional: seed sample data
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000` (API docs at `/docs`).

### Frontend

```bash
cd frontend
npm install
cp .env.example .env        # point to the backend URL
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Project Structure

```
Baseerah/
├── backend/     # FastAPI app, models, services, OCR bill parser, tests
├── frontend/    # React + Vite + Tailwind SPA (Arabic/English)
└── PROPOSAL.md  # full project proposal
```

## License

Private project — all rights reserved.
