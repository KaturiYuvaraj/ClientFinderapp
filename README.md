# AI Client Finder - Full-Stack Chrome Extension & FastAPI Platform

**AI Client Finder** is a production-ready Chrome Extension and FastAPI platform built for freelancers, marketing agencies, and B2B service providers. It empowers professionals to discover potential clients from authorized, public business listings, perform structured AI opportunity evaluations, calculate lead quality scores (0–100), manage sales pipelines, and generate personalized, non-spammy outreach messages.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Features](#2-features)
3. [Architecture](#3-architecture)
4. [Technologies](#4-technologies)
5. [Prerequisites](#5-prerequisites)
6. [MySQL Setup](#6-mysql-setup)
7. [Python Environment Setup](#7-python-environment-setup)
8. [Backend Installation](#8-backend-installation)
9. [Frontend Installation](#9-frontend-installation)
10. [Environment Variables](#10-environment-variables)
11. [Running FastAPI](#11-running-fastapi)
12. [Running React (Dev Mode)](#12-running-react-dev-mode)
13. [Building the Chrome Extension](#13-building-the-chrome-extension)
14. [Loading the Extension into Chrome](#14-loading-the-extension-into-chrome)
15. [Configuring the Business-Data Provider](#15-configuring-the-business-data-provider)
16. [Configuring the AI Provider](#16-configuring-the-ai-provider)
17. [Production Deployment](#17-production-deployment)
18. [Security Considerations](#18-security-considerations)
19. [API Documentation](#19-api-documentation)

---

## 1. Project Overview

Finding prospective clients manually through search engines is tedious and inefficient. **AI Client Finder** automates the discovery workflow legally and ethically. By tapping into authorized business data APIs (e.g. OpenStreetMap public POIs or Google Places API), the platform:
- Analyzes observable business traits (e.g. Missing website, outdated HTTP presence, high footfall/reviews without digital ordering).
- Calculates an objective **Lead Score (0–100)** with confidence ratings.
- Strictly distinguishes **Verified Facts** (observable attributes) from **AI Inferences** (reasoned deductions).
- Generates tailored, professional outreach messages that users review and send manually.

---

## 2. Features

- **Chrome Extension (Manifest V3)**: Compact, sleek popup interface optimized for browser actions, with an expandable full-tab dashboard.
- **Dynamic Search Form**: Search by Service, Category, Location, Radius, and Keywords.
- **Search History**: Saves prior search parameters for quick 1-click query repetition.
- **AI Opportunity Evaluation**:
  - Web Development (identifies missing websites, unsecured HTTP).
  - Branding / Identity (identifies growing businesses lacking cohesive digital identity).
  - Video / Media Editing (detects visual categories with high review engagement).
  - Commercial Photography (identifies dining, retail, and real estate businesses).
- **Facts vs. Inferences Separation**: Clearly marks verified provider data vs. AI suggestions to prevent hallucinations.
- **Lead Pipeline Management**: Full CRUD operations across 6 lifecycle stages: `New`, `Contacted`, `Interested`, `Follow-up`, `Converted`, and `Not Interested`.
- **Duplicate Prevention**: Composite checking across Provider ID, normalized business name, phone number, and address.
- **Analytics Dashboard**: Pipeline funnel visualization, conversion rates, and high-opportunity lead highlights.
- **AI Outreach Drafter**: Generates context-aware, ethical cold outreach pitches with instant copy-to-clipboard.
- **CSV Export**: Full one-click download of all lead attributes, notes, and AI insights.

---

## 3. Architecture

```text
               +-------------------------------------------+
               |        Chrome Extension (Manifest V3)     |
               |       React / JavaScript / Vite / CSS     |
               +---------------------+---------------------+
                                     | HTTPS / JSON
                                     v
               +-------------------------------------------+
               |               FastAPI Backend             |
               |         (Uvicorn, Pydantic, Auth)         |
               +----------+----------+----------+----------+
                          |          |          |
              +-----------+          |          +-----------+
              v                      v                      v
     +-----------------+   +-------------------+   +-----------------+
     | Business Data   |   |   AI Opportunity  |   |    Database     |
     |   Providers     |   |       Service     |   |   (SQLAlchemy)  |
     +-----------------+   +-------------------+   +-----------------+
     | • OpenStreetMap |   | • Google Gemini   |   | • MySQL 8.0     |
     | • Google Places |   | • OpenAI GPT      |   | • SQLite (Dev)  |
     | • Rich Mock     |   | • Deterministic   |   +-----------------+
     +-----------------+   +-------------------+
```

---

## 4. Technologies

### Frontend
- **React 18** (JavaScript JSX, component architecture)
- **Vite 5** (Module bundler configured with relative asset loading)
- **Vanilla CSS** (Custom Slate & Indigo design tokens, glassmorphism, responsive grid)
- **Lucide React** (Modern iconography)
- **Chrome Extension Manifest V3**

### Backend
- **Python 3.9+**
- **FastAPI** (REST API framework with automated OpenAPI docs)
- **Uvicorn** (ASGI high-performance web server)
- **Pydantic v2** (Strict data validation and serialization)
- **SQLAlchemy 2.0** (ORM)
- **PyMySQL & Cryptography** (MySQL drivers)
- **PyJWT & Bcrypt** (JWT security and salted password hashing)
- **HTTPX** (Async HTTP requests for external providers)
- **Pytest** (Automated backend testing suite)

---

## 5. Prerequisites

Before setting up the project, ensure you have:
- **Node.js** (v18+ or v20+) and **npm** installed.
- **Python** (v3.9+ or v3.10+) installed.
- **MySQL Server** (v8.0+) installed and running (optional: SQLite development fallback is built-in).
- **Google Chrome** browser (for loading the extension).

---

## 6. MySQL Setup

1. Open your MySQL terminal or client (e.g. MySQL Workbench, TablePlus):
```bash
mysql -u root -p
```
2. Create the database and tables using the provided DDL script:
```sql
SOURCE c:/Users/YUVARAJ/OneDrive/Desktop/Client Finder/database/schema.sql;
```
Or execute the script directly from the terminal:
```bash
mysql -u root -p < database/schema.sql
```
This initializes the `client_finder` database with the `users`, `leads`, `searches`, and `generated_messages` tables with appropriate indexes and foreign keys.

---

## 7. Python Environment Setup

Navigate to the `backend` folder and create a virtual environment:

### Windows (PowerShell / Command Prompt)
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
```

### macOS / Linux
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

---

## 8. Backend Installation

With your virtual environment activated:
```bash
pip install -r requirements.txt
```

Verify the installation by running the test suite:
```bash
pytest -v
```
All 14 tests should pass with 100% green output.

---

## 9. Frontend Installation

In a separate terminal, navigate to the `extension` folder and install dependencies:
```bash
cd extension
npm install
```

---

## 10. Environment Variables

In `backend/`, copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```

Edit `backend/.env` with your preferred settings:

```env
# Database Configuration
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/client_finder
DATABASE_FALLBACK_SQLITE=true

# Authentication
JWT_SECRET=super_secret_jwt_key_change_in_production_min_32_chars
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# AI Configuration (gemini, openai, rule_based, mock)
AI_PROVIDER=rule_based
AI_API_KEY=your_ai_api_key
AI_MODEL=gemini-1.5-flash

# Business Data Provider (mock, overpass, google_places)
BUSINESS_API_PROVIDER=mock
BUSINESS_API_KEY=your_business_api_key

# Security & CORS
FRONTEND_URL=http://localhost:5173
RATE_LIMIT_PER_MINUTE=60
```

> **Note on Database Fallback**: If MySQL credentials are not yet configured or the MySQL service is temporarily unavailable, `DATABASE_FALLBACK_SQLITE=true` automatically initializes a local `client_finder_dev.db` file so development and testing continue uninterrupted.

---

## 11. Running FastAPI

Start the backend with Uvicorn:
```bash
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```
- API will be live at: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

---

## 12. Running React (Dev Mode)

To run the React application in standard browser dev mode:
```bash
cd extension
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 13. Building the Chrome Extension

To produce production assets for Chrome:
```bash
cd extension
npm run build
```
The compiled extension bundle with `manifest.json`, `index.html`, and `icons/` will be generated in `extension/dist/`.

---

## 14. Loading the Extension into Chrome

1. Open Google Chrome.
2. In the URL bar, go to `chrome://extensions`.
3. Enable **Developer mode** via the toggle switch in the top right.
4. Click the **Load unpacked** button in the top left.
5. In the file picker, select the **`extension/dist`** folder.
6. Click the extension puzzle icon in Chrome and pin **AI Client Finder**.
7. Click the extension icon to launch the popup!

---

## 15. Configuring the Business-Data Provider

The business data layer is modular and configured via `BUSINESS_API_PROVIDER` in `backend/.env`:

| Provider | Setting | Description |
| :--- | :--- | :--- |
| **Mock Provider** | `BUSINESS_API_PROVIDER=mock` | Zero external dependencies. Instant, realistic listings for offline and local testing. |
| **OpenStreetMap Overpass** | `BUSINESS_API_PROVIDER=overpass` | Compliant, live open POI data across global cities (no API key required). |
| **Google Places API** | `BUSINESS_API_PROVIDER=google_places` | Official Google Places API (New Text Search). Requires `BUSINESS_API_KEY`. |

To add a custom business data provider:
1. Inherit from `BusinessDataProvider` in `backend/app/providers/business_provider.py`.
2. Implement the `search(self, query: SearchRequest) -> List[NormalizedBusiness]` method.
3. Register the new class in `get_business_provider()`.

---

## 16. Configuring the AI Provider

The AI evaluation engine is pluggable via `AI_PROVIDER` in `backend/.env`:

| Provider | Setting | Configuration |
| :--- | :--- | :--- |
| **Rule-Based** | `AI_PROVIDER=rule_based` | Deterministic expert scoring algorithm. Operates instantly without external API keys. |
| **Google Gemini** | `AI_PROVIDER=gemini` | Set `AI_API_KEY` with your Gemini API key. Model configurable via `AI_MODEL`. |
| **OpenAI** | `AI_PROVIDER=openai` | Set `AI_API_KEY` with your OpenAI API key (`gpt-4o-mini` default). |

---

## 17. Production Deployment

### Backend
1. Use a production WSGI/ASGI runner like Uvicorn behind Nginx with systemd or Docker.
2. Set a strong `JWT_SECRET` (at least 64 random characters).
3. Connect to a managed MySQL instance (e.g. AWS RDS, Google Cloud SQL).
4. Enforce HTTPS across all endpoints.

### Chrome Extension
1. Update `manifest.json` host permissions to your production backend URL (e.g. `https://api.yourdomain.com/*`).
2. Run `npm run build` in `extension`.
3. Compress the contents of `extension/dist` into a `.zip` archive.
4. Submit to the [Chrome Developer Dashboard](https://chrome.google.com/webstore/devconsole).

---

## 18. Security Considerations

- **No Secrets in Frontend**: All business provider keys and AI API keys reside strictly on the FastAPI server in `.env`.
- **JWT Authentication**: Protected API endpoints require `Authorization: Bearer <token>`. Tokens expire in 7 days by default.
- **Salted Password Hashing**: Passwords are hashed with Bcrypt (cost factor 12).
- **SQL Injection Prevention**: All queries execute through SQLAlchemy parameterized ORM models.
- **Sliding-Window Rate Limiting**: Sensitive routes (`/api/leads/search` and `/api/ai/*`) are throttled per user/IP to avoid API abuse.
- **Compliance & Anti-Spam**: No automated bulk messaging. Users must manually review, copy, and send outreach messages.

---

## 19. API Documentation

When the backend is running, visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

### Core Endpoints

#### Authentication
- `POST /api/auth/register` — Create user account and return JWT.
- `POST /api/auth/login` — Authenticate and receive JWT.
- `GET /api/auth/me` — Retrieve authenticated user profile.

#### Business Search & History
- `POST /api/leads/search` — Search businesses, run AI opportunity scoring, and annotate saved status.
- `GET /api/leads/search-history` — Retrieve previous queries to repeat searches.

#### Leads Pipeline
- `GET /api/leads` — List saved leads (filters: status, service, city, min_score, search query).
- `GET /api/leads/{id}` — Fetch full lead details and opportunity facts.
- `POST /api/leads` — Save new lead with duplicate checking.
- `PUT /api/leads/{id}` — Update lead status, notes, or follow-up date.
- `DELETE /api/leads/{id}` — Remove lead from pipeline.
- `GET /api/leads/export` — Stream CSV download of all saved leads.

#### AI Services
- `POST /api/ai/analyze-lead` — Run opportunity analysis on any business.
- `POST /api/ai/generate-message` — Generate personalized cold outreach message.

#### Dashboard Analytics
- `GET /api/dashboard/stats` — Retrieve lead counts, pipeline distribution, and top opportunities.

---

## License

MIT License. Designed for authorized lead research and ethical client discovery.
