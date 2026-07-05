# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Webhook bridge for the agricultural monitoring system - the upper-computer (上位机) code. Receives sensor data via MQTT webhook from EMQX, stores it in PostgreSQL, and serves a real-time dashboard with SSE push updates.

## Build and Run

**Run the Flask app:**
```bash
python app.py
```

**Test with MQTT mock data:**
```bash
python test_mqtt.py
```

**Environment configuration:**
- Copy `.env.example` to `.env` and configure PostgreSQL connection
- Required: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- Optional: `LOG_FILE_PATH` (default: `logs/webhook.log`)

## Code Architecture

### Directory Structure

```
webhook_bridge/
├── app.py              # Flask application entry point
├── config.py           # Environment configuration (.env via python-dotenv)
├── core/               # Core utilities
│   ├── db.py          # PostgreSQL connection helper
│   ├── sse.py         # Server-Sent Events client management
│   └── logger.py      # Logging setup (console + rotating file)
├── routes/            # Flask blueprints
│   ├── api.py        # RESTful API endpoints
│   └── views.py      # HTML view routes
├── templates/
│   └── dashboard.html # Single-page dashboard UI
├── static/
│   ├── css/style.css  # Dashboard styling
│   └── js/dashboard.js # Frontend logic (Chart.js, SSE, modals)
└── test_mqtt.py       # MQTT mock data generator
```

### Data Flow

1. **Ingestion** (`/api/sensor_data`, POST):
   - Receives JSON payload from EMQX webhook (nested in `payload` field)
   - Extracts sensor fields: `temp`, `air_humi`, `soil_humi`, `light`, `ph`, `co2`, `time` (Unix timestamp)
   - Stores in PostgreSQL `sensor_data` table
   - Broadcasts to all connected SSE clients via `broadcast_sse()`

2. **Real-time Push** (`/api/stream`):
   - SSE endpoint that maintains a queue per client
   - Clients receive updates immediately after new data is stored

3. **Dashboard Updates**:
   - Frontend connects to `/api/stream` on page load
   - Real-time gauge updates via Chart.js
   - Status badges evaluate ranges (e.g., temp 18-28°C = "good")

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sensor_data` | POST | Ingest sensor data (from EMQX webhook) |
| `/api/stream` | GET | SSE real-time data stream |
| `/api/latest` | GET | Latest sensor reading |
| `/api/stats` | GET | 24h aggregation (avg/min/max) |
| `/api/trend` | GET | Historical trend data (time-bucketed) |
| `/api/export` | GET | CSV export with date filtering |
| `/health` | GET | Health check |
| `/dashboard` | GET | Dashboard UI |

### Trend API Time Buckets

The `/api/trend` endpoint supports preset intervals with automatic bucket selection:

| Unit | Time Range | Bucket Size | Limit |
|------|------------|-------------|-------|
| `30m` | 30 minutes | 5 seconds | 360 |
| `1h` | 1 hour | 10 seconds | 360 |
| `6h` | 6 hours | 1 minute | 360 |
| `12h` | 12 hours | 1 minute | 720 |
| `hour` | 24 hours | 1 minute | 1440 |
| `day` | 7 days | 10 minutes | 1008 |
| `week` | 8 weeks | 1 week | 8 |
| `month` | 12 months | 1 month | 12 |
| `year` | 5 years | 1 year | 5 |
| `live` | Last 60 rows | - | 60 |
| `custom` | User-defined | Dynamic (based on delta) | 1000 |

For custom dates, bucket size adjusts automatically: 2+ days = hourly, >60 days = daily, otherwise = minute.

### PostgreSQL Schema

```sql
CREATE TABLE sensor_data (
    time TIMESTAMP,
    temp FLOAT,
    air_humi FLOAT,
    soil_humi FLOAT,
    light FLOAT,
    ph FLOAT,
    co2 FLOAT
);
```

Note: `time` column uses `to_timestamp()` conversion from Unix timestamp on insert.

### Frontend Tech Stack

- **Chart.js 4.4.0** via CDN for charts
- **Server-Sent Events (SSE)** for real-time push
- **Vanilla JavaScript** - no framework
- **CSS custom properties** for theme switching (dark/light)
- **ARIA attributes** for accessibility