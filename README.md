# DTC Automated Bus Scheduling & Route Management System

**Transport Corporation — Operations Hub**
---

A full-stack web application for automated bus scheduling (linked & unlinked duties) and GIS-based route management. Built with Python (Flask) backend and a custom HTML/CSS/JS frontend.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Features](#features)
4. [Tech Stack](#tech-stack)
5. [Project Structure](#project-structure)
6. [Installation & Setup](#installation--setup)
7. [Running the Application](#running-the-application)
8. [API Reference](#api-reference)
9. [Modules Explained](#modules-explained)
10. [Scheduling Algorithms](#scheduling-algorithms)
11. [Route Overlap Detection](#route-overlap-detection)
12. [UI Pages Guide](#ui-pages-guide)
13. [Data Models](#data-models)
14. [Configuration](#configuration)
15. [Future Enhancements](#future-enhancements)

---

## Project Overview

The DTC Operations Hub replaces manual bus scheduling and route planning with an automated software system. It handles:

- **Linked Duty Scheduling** — crew assigned to one bus for the entire shift, no handovers
- **Unlinked Duty Scheduling** — crew rotate across buses with automatic rest period enforcement
- **Route Management** — visual GIS map of all routes with automatic overlap detection for new routes
- **Fleet & Crew Management** — live status tracking for all buses and crew members
- **Dashboard** — real-time summary statistics and operational overview

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Browser (UI)                     │
│         HTML5 + CSS3 + Vanilla JS + Leaflet.js      │
└───────────────────────┬─────────────────────────────┘
                        │ REST API (JSON)
┌───────────────────────▼─────────────────────────────┐
│               Flask Web Server (Python)              │
│                     app.py                          │
└────────────┬──────────────────────┬─────────────────┘
             │                      │
┌────────────▼──────┐   ┌───────────▼─────────────────┐
│  scheduler.py     │   │     route_manager.py         │
│  - Linked Duty    │   │  - Overlap Detection         │
│  - Unlinked Duty  │   │  - Coverage Analysis         │
└───────────────────┘   └─────────────────────────────┘
             │
┌────────────▼──────────────────────────────────────┐
│              In-Memory Data Store                  │
│   buses_db | crews_db | duties_db | routes_db     │
└───────────────────────────────────────────────────┘
```

---

## Features

### Linked Duty Scheduling
- Assign one driver to one bus for an entire shift (Morning / Afternoon / Night / Split)
- Greedy matching algorithm: prefers crew from same depot, then falls back to any available crew
- Generates trip timetable based on route frequency
- Reports unmatched buses, efficiency %, and route coverage %

### Unlinked Duty Scheduling
- Sliding-window crew rotation across the operating day (05:00 – 22:00)
- Enforces minimum 8-hour rest between driving segments
- Enforces maximum 4-hour continuous drive limit per crew member
- Generates full handover timeline for each bus with crew details and rest windows

### Route Management
- Interactive Leaflet.js map centered on Delhi
- Color-coded polylines for all existing routes
- Add new routes via a form with stop list
- Automatic overlap detection: identifies shared stops with existing routes
- Severity levels: High (≥60%), Medium (≥30%), Low (<30%)
- Per-overlap recommendations (merge, stagger, or accept)

### Fleet Management
- Table of all buses with type, depot, capacity, fuel type, and status
- Filter by status (Available / In Service / Maintenance)
- Live search by bus ID

### Crew Management
- Full roster of drivers and conductors
- Filter by role and status
- Live search by name or ID

### Dashboard
- Real-time stats: total buses, available crew, scheduled duties, routes
- Bar charts for fleet and crew status breakdowns
- Route summary panel with distance and trip counts

---

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Python 3.10+, Flask, Flask-CORS     |
| Algorithms | Pure Python (no external ML libs)   |
| Frontend   | HTML5, CSS3, Vanilla JavaScript     |
| Maps       | Leaflet.js 1.9.4 (OSM tiles)        |
| Fonts      | Syne, JetBrains Mono, Inter (Google Fonts) |
| Data Store | In-memory Python dicts (demo mode)  |

---

## Project Structure

```
dtc_system/
│
├── app.py                  # Flask application, all REST endpoints, seed data
├── scheduler.py            # LinkedDutyScheduler + UnlinkedDutyScheduler
├── route_manager.py        # RouteManager — overlap detection, coverage analysis
│
├── templates/
│   └── index.html          # Single-page HTML application shell
│
└── static/
    ├── css/
    │   └── main.css        # Full design system (dark industrial theme)
    └── js/
        └── main.js         # All frontend logic — API calls, rendering, map
```

---

## Installation & Setup

### Prerequisites

- Python 3.10 or higher
- pip package manager
- A modern browser (Chrome, Firefox, Edge)

### 1. Clone / Download the Project

```bash
# If using git
git clone https://github.com/your-repo/dtc-system.git
cd dtc-system

# Or extract the zip and cd into it
cd dtc_system
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv

# Activate on Linux/Mac
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install flask flask-cors pandas numpy scipy
```

Minimal install (if you only want core functionality):

```bash
pip install flask flask-cors
```

---

## Running the Application

```bash
python app.py
```

Then open your browser at:

```
http://localhost:5000
```

You should see the DTC Operations Hub dashboard load with seeded data (30 buses, 40 crew, 5 routes).

---

## API Reference

All endpoints return JSON. Base URL: `http://localhost:5000`

### Dashboard

| Method | Endpoint               | Description                        |
|--------|------------------------|------------------------------------|
| GET    | `/api/dashboard/stats` | Aggregated stats for dashboard     |

### Buses

| Method | Endpoint            | Description                        |
|--------|---------------------|------------------------------------|
| GET    | `/api/buses`        | List all buses (optional `?status=`) |
| GET    | `/api/buses/<id>`   | Get single bus                     |
| PUT    | `/api/buses/<id>`   | Update bus fields                  |

### Crew

| Method | Endpoint            | Description                           |
|--------|---------------------|---------------------------------------|
| GET    | `/api/crews`        | List all crew (optional `?status=`, `?role=`) |
| GET    | `/api/crews/<id>`   | Get single crew member                |

### Scheduling

| Method | Endpoint                  | Description                                  |
|--------|---------------------------|----------------------------------------------|
| POST   | `/api/schedule/linked`    | Generate linked duty schedule                |
| POST   | `/api/schedule/unlinked`  | Generate unlinked duty schedule              |
| GET    | `/api/duties`             | List all generated duties (optional `?type=`) |
| GET    | `/api/duties/<id>`        | Get single duty                              |

**POST `/api/schedule/linked` body:**
```json
{
  "date": "2025-05-13",
  "shift": "Morning"
}
```

**POST `/api/schedule/unlinked` body:**
```json
{
  "date": "2025-05-13"
}
```

### Routes

| Method | Endpoint                  | Description                              |
|--------|---------------------------|------------------------------------------|
| GET    | `/api/routes`             | List all routes                          |
| GET    | `/api/routes/<id>`        | Get single route                         |
| POST   | `/api/routes`             | Create new route (returns overlap info)  |
| DELETE | `/api/routes/<id>`        | Delete a route                           |
| POST   | `/api/routes/overlap`     | Check overlaps without saving            |

**POST `/api/routes` body:**
```json
{
  "name": "Lajpat Nagar → Kashmere Gate",
  "color": "#E74C3C",
  "stops": ["Lajpat Nagar", "INA", "Dhaula Kuan", "Connaught Place", "Kashmere Gate"],
  "distance_km": 18,
  "frequency_min": 12,
  "peak_buses": 4,
  "daily_trips": 55
}
```

---

## Modules Explained

### `app.py`
The Flask application entry point. Responsibilities:
- Registers all REST API routes
- Holds in-memory databases (`buses_db`, `crews_db`, `duties_db`, `routes_db`)
- Calls `seed_data()` on startup to populate demo data
- Delegates scheduling to `scheduler.py` and overlap detection to `route_manager.py`

### `scheduler.py`

#### `LinkedDutyScheduler`
- `generate_schedule(buses, crews, date, shift, routes)` — main entry point
- `_pick_route(routes, depot)` — selects a route for a bus
- `_compute_trips(start, end, route)` — generates trip timetable from route frequency

Algorithm flow:
1. Sort buses by depot
2. Sort crew by depot match + experience (descending)
3. For each bus, find best-matching available crew
4. Assign and generate trip schedule
5. Return duties list + summary stats

#### `UnlinkedDutyScheduler`
- `generate_schedule(buses, crews, date, routes)` — main entry point
- `_schedule_bus_day(bus, crews, crew_timeline, route, date, start_hour)` — per-bus rotation

Algorithm flow:
1. Track each crew member's `last_end` and `rest_until` times
2. For each bus, loop through the day window (05:00–22:00)
3. Assign the next rested crew for a max-4-hour drive window
4. Mark crew as resting for 8 hours after each segment
5. Build handover timeline with trip details per segment

### `route_manager.py`

#### `RouteManager`
- `find_overlaps(candidate, existing_routes)` — compares stop sets
- `_severity(pct)` — maps overlap % to High/Medium/Low
- `_find_contiguous_segments(...)` — finds runs of consecutive shared stops
- `_recommend(severity, pct, route)` — generates actionable text recommendation
- `optimize_coverage(routes)` — classifies stops as over/adequately/under-served

---

## Scheduling Algorithms

### Linked Duty — Greedy Depot-Match

```
Input:  N buses, M crew, shift window, routes
Output: duty assignments with trip timetables

For each bus (sorted by depot):
  Find crew with matching depot and Available status
  If none found, take any Available crew
  Assign crew to bus for full shift
  Generate trip list from route frequency
  Record unmatched buses if no crew available
```

**Complexity:** O(N × M) worst case, O(N log M) with depot pre-grouping

**Key constraints:**
- One crew per bus
- Crew can only be assigned once
- Trip intervals derived from route frequency

### Unlinked Duty — Sliding Window Rotation

```
Input:  N buses, M crew, full day window
Output: handover timeline per bus with rest compliance

For each bus:
  current_time = 05:00
  While current_time < 22:00:
    Find next crew whose rest_until <= current_time
    Assign 4-hour drive window
    Generate trips within that window
    Set crew.rest_until = drive_end + 8 hours
    Advance current_time to drive_end
```

**Complexity:** O(N × D × M) where D = day segments (~4)

**Key constraints:**
- Max continuous drive: 4 hours
- Min rest before reassignment: 8 hours
- Crew tracked across all buses (global timeline)

---

## Route Overlap Detection

The `RouteManager.find_overlaps()` method uses **stop-name intersection**:

```
candidate_stops = {"stop_a", "stop_b", "stop_c", ...}
existing_stops  = {"stop_b", "stop_c", "stop_d", ...}
common          = candidate_stops ∩ existing_stops
overlap_pct     = |common| / |candidate_stops| × 100
```

**Severity thresholds:**
- `High`   — ≥ 60% stops overlap → consider merging or rerouting
- `Medium` — 30–59% → stagger departure times
- `Low`    — < 30% → acceptable connectivity overlap

**Contiguous segment detection** finds consecutive runs of shared stops in the candidate's stop order, identifying the actual corridor of overlap rather than scattered individual stops.

---

## UI Pages Guide

| Page            | What you can do                                                                 |
|-----------------|---------------------------------------------------------------------------------|
| **Dashboard**   | See live bus/crew/duty/route stats, fleet and crew status charts                |
| **Linked Duties** | Pick a date + shift, click Generate, view full assignment table              |
| **Unlinked Duties** | Pick a date, click Generate, expand each bus to see crew handover timeline |
| **Route Manager** | View all routes on map, add new route, see overlap analysis automatically   |
| **Fleet**       | Browse all buses, filter by status, search by ID                                |
| **Crew**        | Browse all crew, filter by role/status, search by name                          |

---

## Data Models

### Bus
```json
{
  "id": "DTC-1001",
  "type": "Low-Floor AC",
  "depot": "Rohini Depot",
  "status": "Available",
  "capacity": 55,
  "fuel_type": "CNG"
}
```

### Crew
```json
{
  "id": "CREW-201",
  "name": "Rajesh Kumar",
  "role": "Driver",
  "depot": "Rohini Depot",
  "shift": "Morning",
  "status": "Available",
  "license": "DL45231",
  "experience_years": 8
}
```

### Linked Duty
```json
{
  "id": "LD-A1B2C3",
  "type": "linked",
  "date": "2025-05-13",
  "shift": "Morning",
  "bus_id": "DTC-1001",
  "crew_id": "CREW-201",
  "crew_name": "Rajesh Kumar",
  "route_id": "R-001",
  "start_time": "05:00",
  "end_time": "13:00",
  "trips": [...],
  "total_distance_km": 224,
  "status": "Scheduled"
}
```

### Unlinked Duty
```json
{
  "id": "UL-D4E5F6",
  "type": "unlinked",
  "bus_id": "DTC-1005",
  "route_id": "R-002",
  "handovers": [
    {
      "crew_id": "CREW-205",
      "crew_name": "Amit Singh",
      "from_time": "05:00",
      "to_time": "09:00",
      "rest_until": "17:00",
      "trips": [...]
    }
  ],
  "total_trips": 6,
  "crew_count": 3
}
```

### Route
```json
{
  "id": "R-001",
  "name": "Rohini Sec-7 → ISBT Kashmere Gate",
  "color": "#E74C3C",
  "stops": ["Rohini Sec-7", "Pitampura", "..."],
  "distance_km": 28,
  "frequency_min": 8,
  "peak_buses": 6,
  "daily_trips": 85
}
```

---

## Configuration
----------------------------------------------------------------------

All configuration is currently inline in `app.py` and `scheduler.py`. Key values to adjust:

| Setting                        | Location           | Default |
|--------------------------------|--------------------|---------|
| `MIN_REST_HOURS`               | `scheduler.py`     | 8       |
| `MAX_CONTINUOUS_DRIVE_HOURS`   | `scheduler.py`     | 4       |
| `TRIP_DURATION_MINUTES`        | `scheduler.py`     | 90      |
| Flask `port`                   | `app.py` bottom    | 5000    |
| Number of seed buses           | `seed_data()`      | 30      |
| Number of seed crew            | `seed_data()`      | 40      |

To connect a real database, replace the `buses_db`, `crews_db`, `duties_db`, `routes_db` dicts in `app.py` with SQLAlchemy models or a PostgreSQL/MySQL connection.

---

## Future Enhancements

- **Persistent Database** — PostgreSQL + SQLAlchemy ORM for production data
- **Real GIS Routing** — OSRM or Google Maps API for actual road-network route drawing
- **Optimization Engine** — ILP (Integer Linear Programming) using PuLP for optimal crew-bus matching
- **Real-time Updates** — WebSocket support for live duty status changes
- **Authentication** — Role-based login (Scheduler / Planner / Manager)
- **Export** — PDF/Excel export for duty rosters and route reports
- **Mobile App** — PWA for crew to view their assigned duties on mobile
- **Notifications** — SMS/email alerts for schedule changes and rest period warnings
- **Historical Analytics** — Trip performance, delay tracking, fuel consumption reports

-----

---

*Built for DTC Operations — Automated Bus Scheduling & Route Management System*
