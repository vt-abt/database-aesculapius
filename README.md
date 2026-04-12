# Second-Life Medical Records

A patient-centric, immutable database system for lifelong medical history tracking, built for a 2nd-year DBMS academic project.

## Features
- **Immutable Records:** Database triggers prevent any updates or deletions of medical histories.
- **Patient Ownership:** Time-bound consent mechanism controls which doctors can view records.
- **Traceability:** Corrections are appended as new entries linked to previous records via self-referencing foreign keys.
- **Live Audit Trail:** Every action and SQL query is logged and visible in a real-time terminal.
- **India-Specific Details:** Includes Blood Group and DOB (dynamically calculated age) for realistic hospital registration.

## Tech Stack
- **Database:** MySQL
- **Backend:** Python (Flask)
- **Frontend:** HTML/CSS (Jinja2 Templates)

## Setup Instructions

1. **Database Setup:**
   Ensure MySQL is running locally.
   ```sql
   CREATE DATABASE second_life_mr;
   USE second_life_mr;
   SOURCE database/schema.sql;
   ```

2. **Install Dependencies:**
   Requires Python 3.10+.
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application:**
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` in your browser.

## Test Credentials
- **Admin:** `admin` / `passkey_12345`
- **Patient:** `patient_zero` / `pat123`
- **Doctor (Cardio):** `trehan` / `doctor_12345`
*(See schema.sql for the full list of doctors)*