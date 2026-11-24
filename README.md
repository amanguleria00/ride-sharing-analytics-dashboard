# Ridewise – Ride-Sharing Analytics Dashboard

A full-stack analytics dashboard designed to monitor and analyze ride-sharing operations. It provides insights into ride activity, driver performance, revenue, vehicle distribution and customer demand through interactive charts and visualizations.

## Features

- **Dashboard Overview:** Total rides, completed rides, cancelled rides, revenue and average fare.
- **Revenue Analysis:** Track revenue trends over time.
- **Ride Status Analysis:** Monitor completed, ongoing, requested and cancelled rides.
- **Vehicle Analysis:** Analyze rides by vehicle type.
- **Driver Performance:** Identify top-performing drivers.
- **Peak Hour Analysis:** Identify the busiest hours for ride requests.
- **Payment Analysis:** View successful payments by payment method.
- **Ride Records:** Browse and filter individual ride details.

## Technologies Used

| Component | Technology |
|---|---|
| Frontend | Vue 3, Vite, Axios |
| Backend | Python, Flask, Flask-CORS |
| Database | SQLite |
| Charts | Chart.js, vue-chartjs |

## Project Structure

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
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Database

The project uses SQLite to store and manage ride-sharing data.

The database contains five main tables:

- **Riders:** Customer information.
- **Drivers:** Driver details.
- **Vehicles:** Vehicle information.
- **Rides:** Ride bookings and trip details.
- **Payments:** Payment transactions.

The database is initialized locally using sample data consisting of 20 riders, 12 drivers and vehicles, and 150 rides.

## Installation and Setup

### Prerequisites

- Python 3
- Node.js and npm
- Git

### 1. Clone the repository

```bash
git clone https://github.com/amanguleria00/ride-sharing-analytics-dashboard.git
cd ride-sharing-analytics-dashboard
```

### 2. Start the Backend

Open a terminal:

```bash
cd backend
py -3 -m venv venv
```

For Windows PowerShell, activate the environment:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Install dependencies and initialize the database:

```bash
pip install -r requirements.txt
python init_db.py
python app.py
```

The backend runs at:

`http://127.0.0.1:5000`

### 3. Start the Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL displayed in the terminal, normally:

`http://localhost:5173`

**Note:** Keep both backend and frontend servers running while using the dashboard.

## API Endpoints

| Endpoint | Description |
|---|---|
| `/api/health` | Check API status |
| `/api/dashboard/summary` | Dashboard statistics |
| `/api/dashboard/revenue-trend` | Revenue trends |
| `/api/dashboard/rides-by-status` | Ride status distribution |
| `/api/dashboard/rides-by-vehicle` | Vehicle analysis |
| `/api/dashboard/top-drivers` | Top driver performance |
| `/api/dashboard/peak-hours` | Peak ride request hours |
| `/api/dashboard/payment-methods` | Payment distribution |
| `/api/rides` | Ride records |

## Data Analytics

All dashboard metrics and chart datasets are dynamically calculated from the SQLite database using SQL queries. Revenue calculations include successful payments associated with completed rides only.

The project uses a locally generated database with deterministic sample data. The database file is excluded from GitHub and can be recreated using:

```bash
python init_db.py
```

## Purpose

The main objective of Ridewise is to transform raw ride-sharing data into meaningful business insights, helping understand operational performance, monitor revenue, evaluate driver activity and identify customer demand patterns.
