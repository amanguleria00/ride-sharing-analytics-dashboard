# Ridewise — Ride-Sharing Analytics Dashboard

A full-stack operations dashboard for exploring ride activity, fleet mix, driver performance, successful-payment revenue, and request patterns. The Vue 3 client fetches all business metrics from a Flask REST API backed by a normalized SQLite database; dashboard metrics and chart datasets are not hardcoded.

## Architecture

- **Frontend:** Vue 3, Vite, Axios, Chart.js and vue-chartjs.
- **Backend:** Python 3, Flask, Flask-Cors and parameterized `sqlite3` queries.
- **Storage:** SQLite. The development database is generated locally and excluded from version control.
- **Seed data:** deterministic 20 riders, 12 drivers and vehicles, and 150 rides with a payment per ride. Initialization can be repeated without duplicating rows.

## Project structure

```text
ride_sharing_app/
├── backend/
│   ├── app.py
│   ├── controller.py
│   ├── persistence.py
│   ├── init_db.py
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── services/
│   │   └── views/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

## Database schema and metric definitions

`riders` has many `rides`; each ride references one rider, driver, and vehicle. `vehicles.driver_id` links the assigned vehicle to its driver. A ride has at most one payment. Foreign keys are enabled on application connections and the schema has checks for permitted values and indexes for date, status, driver, vehicle, and payment-status filters.

Dates use ISO-8601 text (`YYYY-MM-DDTHH:MM`). Ride statuses are `requested`, `ongoing`, `completed`, and `cancelled`. Driver status is `active` or `inactive`; payment status is `successful`, `failed`, or `refunded`. Payment methods are `Card`, `Cash`, `Wallet`, and `UPI`.

- **Total/completed/cancelled rides:** ride row counts for the selected request date range.
- **Total revenue:** successful payments joined to completed rides only. Failed/refunded payments are excluded. Payment totals are aggregated without joining payments into ride-count metrics.
- **Average fare:** average `rides.fare` across completed rides (not payment amount); zero when there are no completed rides.
- **Cancellation rate:** cancelled rides divided by all rides in the selected date range, as a percentage; zero for an empty range.
- **Trends and grouped charts:** revenue trends include completed rides with successful payment only; ride status and vehicle counts include rides in any status.
- **Top drivers:** completed ride count and revenue from successful payments on completed rides.
- **Peak hours:** rides grouped by request-time hour. Payment-method distribution includes successful payments only.

## API

All successful responses are JSON with a `data` property. Validation errors use HTTP 400 and `{"error":{"message":"..."}}`; missing database returns HTTP 503; query failures return HTTP 500. Optional `start_date` and `end_date` parameters use `YYYY-MM-DD`, are inclusive, and apply to ride request dates.

| Method / path | Purpose | Additional parameters |
| --- | --- | --- |
| `GET /api/health` | API health | — |
| `GET /api/dashboard/summary` | KPI metrics | date range |
| `GET /api/dashboard/revenue-trend` | Daily revenue series | date range, `granularity=daily\|monthly` (default `daily`) |
| `GET /api/dashboard/rides-by-status` | Ride counts by status | date range |
| `GET /api/dashboard/rides-by-vehicle` | Ride counts by vehicle type | date range |
| `GET /api/dashboard/top-drivers` | Top drivers by completed ride count and revenue | date range, `limit` 1–50 (default 10) |
| `GET /api/dashboard/peak-hours` | Ride requests per hour | date range |
| `GET /api/dashboard/payment-methods` | Successful payment distribution | date range |
| `GET /api/rides` | Paginated ride details | date range, `status`, `vehicle_type`, `page` (default 1), `per_page` (default 10, max 100) |

Example:

```json
{
  "data": {
    "total_rides": 150,
    "completed_rides": 98,
    "cancelled_rides": 26,
    "total_revenue": 23661.9,
    "average_fare": 262.79,
    "cancellation_rate": 17.33
  }
}
```

These are the calculated values from the included sample database; the API computes them from the selected records.

Ride-list example:

```json
{
  "data": {
    "items": [
      {
        "ride_id": 1,
        "pickup_location": "Connaught Place",
        "dropoff_location": "Koramangala",
        "request_time": "2025-01-01T13:13",
        "distance_km": 3.6,
        "fare": 91.8,
        "status": "completed",
        "driver_name": "Raj Malhotra",
        "vehicle_type": "Sedan",
        "payment_method": "Card",
        "payment_status": "successful"
      }
    ],
    "page": 1,
    "per_page": 10,
    "total": 150,
    "total_pages": 15
  }
}
```

## Setup and run

Run backend and frontend in separate terminals. Commands below start from the `ride_sharing_app` directory.

### Windows PowerShell

```powershell
cd .\backend
py -3 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python init_db.py
python app.py
```

In another PowerShell terminal:

```powershell
cd .\frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal (normally `http://127.0.0.1:5173`).
If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again.

### macOS / Linux

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python init_db.py
python app.py
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

### Reset or choose a database

`python init_db.py` creates the schema and inserts missing fixed-ID sample rows; running it again is safe and does not duplicate the sample records. To fully reset, stop the Flask server, delete only `backend/ride_sharing.db`, then run `python init_db.py` again. To initialize an alternate database, run `python init_db.py --database path\to\test.db`. To make Flask use it, set `RIDE_SHARING_DATABASE` to that path before starting the server.

The frontend uses Vite's `/api` proxy to `http://127.0.0.1:5000`. Set `VITE_API_BASE_URL` in a local `frontend/.env.local` only if a different API base URL is required; do not put secrets in frontend environment variables.

## Tests

Tests use a temporary SQLite file and do not modify the development database:

```powershell
cd .\backend
.\venv\Scripts\Activate.ps1
python -m unittest discover -s tests -v
```

```bash
cd backend
source venv/bin/activate
python -m unittest discover -s tests -v
```

The tests cover repeatable seeding, foreign keys, summary calculation against SQL, date/status/pagination filters, invalid parameters, empty periods, and API endpoints.

## Troubleshooting

- **Database not initialized (503):** from `backend`, activate the venv and run `python init_db.py`.
- **Dashboard cannot reach API:** start Flask on port 5000 before Vite; the Vite server proxies `/api` to that port.
- **Port conflict:** choose another Flask port with `PORT=5001` (PowerShell: `$env:PORT='5001'`) and update `frontend/vite.config.js` proxy target.
- **No chart or ride records:** check the selected date range. The dashboard initially displays all available records; the seeded records currently span January through March 2025.
- **Dependency install issues:** verify Python 3 and Node.js/npm are installed, then rerun the relevant package-manager install command.
