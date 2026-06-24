# Uptime Monitoring Service

A production-grade Uptime Monitoring Service to monitor websites/APIs, track uptime and latency, store historical data, and trigger alerts when failures occur.

## Features
- Add URLs with customizable polling frequency (as low as 10s)
- Support for GET and HEAD requests via asynchronous monitoring engine
- High scalability with `aiohttp` for max concurrency and `APScheduler`
- Measures Time to First Byte (TTFB) and Response Time
- Schedulers run independently in an asyncio background loop
- SQLite database backing via SQLAlchemy
- Modern responsive dashboard using Flask and Chart.js
- Configurable Email/Webhook alerts with cooldown protections

## Requirements
- Python 3.9+
- See `requirements.txt`

## Setup Instructions

1. **Create and Activate Virtual Environment** (Optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate
   # or on Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the dashboard:**
   Open your browser and navigate to `http://localhost:5000`

## Alert Configuration
Alerts uses SMTP or Webhooks. To send emails, configure the Environment variables before starting `app.py`:
- `SMTP_SERVER`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASS`
- `SMTP_FROM`

## Architecture Overview
- **app.py**: Flask web application exposing REST API and serving the dashboard UI.
- **scheduler.py**: APScheduler instance executing monitors periodically in a non-blocking background thread.
- **monitor.py**: Asynchronous fetch functions handling redirects, timeouts, and metrics collection.
- **database.py / models.py**: Clean ORM layer for tracking configuration and log telemetry.
- **alerts.py**: Alert delivery manager integrating SMTP/Webhooks logic with spam prevention.
