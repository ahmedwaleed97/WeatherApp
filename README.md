# Climo — Weather App

A full-stack weather app that shows live weather, a 5-day forecast, air quality, UV index, and a Wikipedia snippet for any city in the world. You can search by city name, ZIP code, GPS coordinates, or tap anywhere on a map.

---

## What it does

- Auto-detects your location when you open it
- Search any city, landmark, ZIP code, or GPS coordinates
- Live weather pulled from OpenWeatherMap
- 5-day forecast with rain chance, wind, and temperature
- UV index with plain-English advice ("No sunscreen needed", "Stay indoors at midday")
- Air quality with human labels ("Go Outside!", "A Bit Iffy", "Stay In!")
- A short Wikipedia description of whatever city you're viewing
- Interactive dark map — tap anywhere to get weather for that spot
- Save locations and reload them later
- Export your saved weather records to CSV, Excel, or JSON

---

## Tech Stack

### Frontend
| What | Why |
|------|-----|
| **Vue 3** | The UI framework — handles all the interactive parts |
| **Vite** | The build tool — fast development server, bundles for production |
| **Leaflet.js** | The map library — renders the interactive dark map |
| **Outfit** (Google Font) | The app's typeface — modern and readable |
| **OpenStreetMap + CARTO** | Free dark map tiles used inside Leaflet |

### Backend
| What | Why |
|------|-----|
| **FastAPI** | Python web framework — handles all the API endpoints |
| **PostgreSQL** | The database — stores saved weather records |
| **SQLAlchemy** | Talks to the database from Python |
| **Pydantic** | Validates incoming data before it hits the database |
| **httpx** | Makes HTTP requests to external weather APIs |
| **openpyxl** | Generates Excel exports |
| **Docker** | Runs the PostgreSQL database in a container |

### External APIs
| What | Used for |
|------|----------|
| **OpenWeatherMap** | Live weather, 5-day forecast, air quality, geocoding |
| **Open-Meteo** | Historical weather, extended forecasts, UV index (no API key needed) |
| **Wikipedia REST API** | City description card (called directly from the browser, no key needed) |

---

## Folder Structure

```
WeatherApp/
│
├── backend/                    ← Python API server
│   ├── app/
│   │   ├── main.py             ← App entry point, CORS, startup
│   │   ├── config.py           ← Reads environment variables (.env)
│   │   ├── database.py         ← Database connection setup
│   │   │
│   │   ├── models/
│   │   │   └── weather.py      ← Database table definition
│   │   │
│   │   ├── schemas/
│   │   │   └── weather.py      ← Input/output data shapes & validation
│   │   │
│   │   ├── routers/
│   │   │   └── weather.py      ← All API endpoints (create, read, update, delete, export)
│   │   │
│   │   ├── services/
│   │   │   ├── geocoding.py    ← Turns a city name into GPS coordinates
│   │   │   ├── openweathermap.py ← Calls the OpenWeatherMap API
│   │   │   └── weather_api.py  ← Blends data from multiple sources into one result
│   │   │
│   │   └── utils/
│   │       └── export.py       ← CSV, Excel, and JSON export logic
│   │
│   ├── docker-compose.yml      ← Starts the PostgreSQL database
│   ├── requirements.txt        ← Python packages to install
│   ├── .env                    ← Your secrets (not committed to git)
│   └── .env.example            ← Template showing what goes in .env
│
├── frontend/                   ← Vue 3 app
│   ├── src/
│   │   ├── App.vue             ← Root component — layout, navigation, state
│   │   ├── main.js             ← Mounts the Vue app
│   │   ├── api.js              ← All calls to the backend + Wikipedia
│   │   ├── utils.js            ← Shared helpers (emojis, labels, UV, AQI, formatting)
│   │   │
│   │   └── components/
│   │       ├── WeatherHero.vue   ← Big weather icon, temperature, description
│   │       ├── StatsRow.vue      ← Wind / Rain Chance / Humidity strip
│   │       ├── ForecastStrip.vue ← 5-day horizontal forecast cards
│   │       ├── SearchModal.vue   ← Search sheet with autocomplete
│   │       ├── SavedView.vue     ← List of saved locations
│   │       ├── MapView.vue       ← Interactive map (click to get weather)
│   │       ├── BottomNav.vue     ← Bottom navigation bar
│   │       └── ErrorBanner.vue   ← Error message with dismiss button
│   │
│   ├── index.html              ← HTML shell, loads fonts
│   ├── vite.config.js          ← Build config, chunk splitting
│   ├── .env                    ← Your frontend config (not committed)
│   └── .env.example            ← Template showing what goes in .env
│
├── .gitignore                  ← Files git will never commit (secrets, builds)
└── README.md                   ← This file
```

---

## How to Run It

You need these installed first:
- [Node.js](https://nodejs.org) (v18 or newer)
- [Python](https://python.org) (v3.11 or newer)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

---

### Step 1 — Start the database

```bash
cd backend
docker compose up -d
```

This starts PostgreSQL on port `5433`. The data persists in a Docker volume between restarts.

---

### Step 2 — Set up the backend

```bash
cd backend

# Create a Python virtual environment
python -m venv venv

# Activate it
source venv/bin/activate        # Mac / Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Create your .env file
cp .env.example .env
# Then open .env and fill in your OpenWeatherMap API key
```

**Get a free OpenWeatherMap API key:** Sign up at [openweathermap.org](https://openweathermap.org/api), go to API keys, copy your key, and paste it into `backend/.env`.

> Note: New keys take up to 2 hours to activate after signing up.

```bash
# Start the backend server
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`
You can explore all endpoints at `http://localhost:8000/docs`

---

### Step 3 — Set up the frontend

Open a new terminal tab:

```bash
cd frontend

# Install dependencies
npm install

# Create your .env file
cp .env.example .env
# The default (http://localhost:8000) is correct for local development

# Start the dev server
npm run dev
```

The app opens at `http://localhost:5173`

---

### Building for production

```bash
cd frontend
npm run build
```

The production-ready files go into `frontend/dist/`. Deploy that folder to any static host (Netlify, Vercel, Cloudflare Pages, etc.).

For the backend in production, set `CORS_ORIGINS` in your `.env` to your frontend's actual URL:

```
CORS_ORIGINS=["https://your-app.com"]
```

---

## API Endpoints

| Method | Endpoint | What it does |
|--------|----------|--------------|
| `POST` | `/weather/` | Search a location, fetch weather, save it |
| `GET` | `/weather/` | List all saved records |
| `GET` | `/weather/{id}` | Get one saved record |
| `PUT` | `/weather/{id}` | Update a record |
| `DELETE` | `/weather/{id}` | Delete a record |
| `GET` | `/weather/locations?q=...` | Search for location autocomplete |
| `GET` | `/weather/{id}/export?format=csv` | Export one record |
| `GET` | `/weather/export/all?format=excel` | Export all records |

---

## Environment Variables

### Backend (`backend/.env`)

```
DATABASE_URL=postgresql://weather_user:weather_pass@127.0.0.1:5433/weather_db
OPENWEATHERMAP_API_KEY=your_key_here
CORS_ORIGINS=["http://localhost:5173"]
```

### Frontend (`frontend/.env`)

```
VITE_API_URL=http://localhost:8000
```
