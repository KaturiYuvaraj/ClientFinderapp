# AI Client Finder - Backend

FastAPI backend providing authorized B2B lead discovery, AI opportunity analysis, lead management, and personalized outreach message generation.

## Features
- **Authentication**: JWT-based auth with bcrypt password hashing.
- **Pluggable Business Data Provider**: Compliant OpenStreetMap Overpass API, Google Places API adapter, and rich Mock provider.
- **AI Opportunity Engine**: Evaluates business signals, assigns 0–100 opportunity score, distinguishes verified facts from inferences, and drafts personalized outreach.
- **Lead Pipeline Management**: Full CRUD, duplicate prevention (by provider ID, normalized name, phone, address), status tracking, notes, and follow-up dates.
- **CSV Export**: Export filtered leads with full business and AI evaluation data.
- **Rate Limiting**: Sliding-window rate limiting to prevent API abuse.

## Setup & Running

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env

# 5. Start development server
uvicorn app.main:app --reload --port 8000
```

Interactive API documentation will be available at `http://localhost:8000/docs`.

## Running Tests
```bash
pytest -v
```
