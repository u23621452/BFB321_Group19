# StockFlow Engine

A web application for **Penbro Kelnick (Pty) Ltd**, a South African manufacturer of industrial transformers, power supplies and sheet-metal enclosures. StockFlow connects the three places where a work order lives (reception, the storeroom and the shop floor) so that material shortages are seen days before assembly instead of the afternoon before.

**Project:** StockFlow Engine, final project for **BFB 321** (University of Pretoria)
**Group:** BFB321_Group19

## Team

| Member | Student number | GitHub |
|---|---|---|
| Heinrich Willem Fourie | u23621452 | [u23621452](https://github.com/u23621452) |
| Tiaan Behr | u22710443 | [u22710443](https://github.com/u22710443) |

### Who led what

| Member | Led |
|---|---|
| **Heinrich Willem Fourie** | The supply chain model (EOQ, safety stock, reorder point, reservation) and its unit tests. Database models, migrations, `schema.sql` and the ER diagram. Login, inventory, material request and queue endpoints. The job service with soft reservation, and the pick service and stock ledger. The base template, dashboard, job files and scanner pages. The OpenAPI description. Seed data. |
| **Tiaan Behr** | Validation for jobs and picks. The jobs, picks and KPI endpoints. The storeroom queue with order-by dates. Central error handling and config. Test fixtures, and the pick, request, OpenAPI and integration tests. The login, queue and inventory pages and scripts. The shared JavaScript helpers and the job detail pop-up. The API docs and Swagger page. The schema generator script. |

Both members committed across most areas (tests, pages, services and models), so the table shows who led each part. The commit history on GitHub (Insights, then Contributors) is the full record.

> **About the data.** All jobs, customers and BOMs are made up. Stock items are *demo data modelled on a storeroom like Penbro Kelnick's*. The company did not allow us to use its data, so nothing here is confidential company data.

---

## What it does

| Role | What they do in the app |
|---|---|
| **Reception** | Opens a job file with its Bill of Materials. Stock is *soft-reserved* immediately and any shortage is flagged. Can change a job's start date, priority, customer or description. |
| **Storeroom** | Sees a 7- or 14-day queue of upcoming jobs, with shortage alerts, an **order-by date** (start date minus supplier lead time) and a suggested order quantity from the supply chain model. Closes material requests. |
| **Operator** | Uses a phone-friendly scanner page to confirm picks. Every pick writes a row to the stock ledger and updates the job. They can also request extra material. |
| **Admin** | Can use everything. |

The supply chain logic (EOQ, safety stock at a 95 % service level, reorder point, soft reservation, lookahead) lives in `models/stock_model.py`. It is plain Python with no Flask or database imports, and it has its own unit tests. The API calls it from `app/services/`.

## The three end-to-end flows

**1. Reception opens a job and stock is reserved.** Reception fills in the job form with its BOM lines. The API checks the stock, reserves it in start-date order, saves the job in MySQL and returns the status `reserved` or `shortage`.

**2. The storeroom sees the shortage in the queue, with an order-by date.** The queue page lists jobs starting in the next 7 or 14 days. Short items show how many are missing, the date to order by, an "Expedite now" flag if that date has passed, and a suggested order quantity.

**3. The operator confirms a pick on the shop floor and the ledger updates.** On a phone-width page the operator picks a work order, scans or types a code and confirms the quantity. Stock drops, a ledger row is written, the job status updates, and a pick that is more than the job needs is refused.

The flows are connected. A job created by reception appears in the storeroom's queue and on the operator's scanner, and a pick changes the inventory page and the dashboard numbers.

### Screenshots

| | |
|---|---|
| ![Login](docs/screenshots/01-login.png) | ![Dashboard](docs/screenshots/02-dashboard.png) |
| Login, with demo accounts | Dashboard KPIs |
| ![Job file created](docs/screenshots/03-flow1-job-file-created.png) | ![Job detail](docs/screenshots/04-job-detail.png) |
| Flow 1: job file created, shortage reported | Job detail with BOM lines |
| ![Queue 7 days](docs/screenshots/05-flow2-storeroom-queue.png) | ![Queue 14 days](docs/screenshots/06-queue-14-days.png) |
| Flow 2: storeroom queue, next 7 days | Next 14 days |
| ![Inventory](docs/screenshots/07-inventory.png) | ![API docs](docs/screenshots/14-api-docs.png) |
| Inventory with reservations | Swagger page for the API |

### Empty and error states

Every list and form handles the states a user can meet. When there is nothing to show, the table says so. When the server cannot be reached, it shows the problem with a **Try again** button.

| Empty | Error (with retry) |
|---|---|
| ![Empty](docs/screenshots/08-state-empty.png) | ![Error](docs/screenshots/09-state-error.png) |

Scanner page (flow 3):

| Scanner | Pick panel | After confirming |
|---|---|---|
| ![Scanner](docs/screenshots/11-flow3-scanner.png) | ![Pick](docs/screenshots/12-scanner-pick.png) | ![Picked](docs/screenshots/13-scanner-picked.png) |

## Setup (runbook)

You need **Python 3.11 or newer**, **Git** and **MySQL 8**. These are the exact commands for Windows PowerShell; on macOS or Linux use `python3` and `source venv/bin/activate`.

### 1. Get the code and install the packages

```powershell
git clone https://github.com/u23621452/BFB321_Group19.git
cd BFB321_Group19

python -m venv venv
venv\Scripts\activate

python -m pip install -r requirements.txt
```

### 2. Create the MySQL database

Open the MySQL prompt with `mysql -u root -p` and run:

```sql
CREATE DATABASE stockflow CHARACTER SET utf8mb4;
CREATE USER 'stockflow'@'localhost' IDENTIFIED BY 'StockFlowPass1';
GRANT ALL PRIVILEGES ON stockflow.* TO 'stockflow'@'localhost';
EXIT;
```

### 3. Create your settings file

```powershell
copy .env.example .env
```

Open `.env` and set the database line (the MySQL line, with the SQLite line commented out):

```
# DATABASE_URL=sqlite:///stockflow.db
DATABASE_URL=mysql+pymysql://stockflow:StockFlowPass1@localhost/stockflow
```

### 4. Build the tables and load the demo data

```powershell
python -m flask --app app db upgrade
python seed.py
```

### 5. Start the app

```powershell
python app.py
```

Open **http://127.0.0.1:5000** and log in with a demo account. The password for all four is `Password123` (set by `DEMO_PASSWORD` in `.env`):

| Account | Role |
|---|---|
| `reception@stockflow.test` | opens job files |
| `storeroom@stockflow.test` | plans the queue |
| `operator@stockflow.test` | shop-floor picks |
| `admin@stockflow.test` | everything |

The page styles come from a CDN (Bootstrap), so the browser needs an internet connection.

**API documentation:** http://127.0.0.1:5000/api/docs (Swagger page) and `docs/openapi.json` (the OpenAPI 3 file).

**No MySQL?** Leave `DATABASE_URL` as the SQLite line in `.env.example` and skip step 2. Everything else is the same. All automated tests use SQLite.

### Resetting the demo

`python seed.py` empties the tables and loads the demo data again. Job start dates are set **relative to the day you run it**, so run it again on demo day to keep the queue full.

### Running the tests

```powershell
python -m pytest
```

There are **101 tests**: supply chain model unit tests, API tests for every endpoint, page-access tests, integration tests that walk through each flow (`tests/test_flows.py`) and a test that checks the OpenAPI file against the real routes. They run on an in-memory SQLite database, so they never touch your real data.

---

## Configuration

Settings come from `config.py` (development, testing and production classes) and from a `.env` file. `.env.example` lists every setting and contains no secrets. The real `.env` is never committed.

| Setting | Meaning |
|---|---|
| `APP_ENV` | `development`, `testing` or `production` |
| `SECRET_KEY` | Signs the login session cookie. Use a long random value in production. |
| `DATABASE_URL` | MySQL: `mysql+pymysql://user:password@localhost/stockflow`. SQLite is the fallback (`sqlite:///stockflow.db`). |
| `DEMO_PASSWORD` | Password `seed.py` gives the four demo accounts. |

## Database

Six tables, with `created_at` and `updated_at` on each. Foreign keys, unique keys and check constraints (stock on hand cannot be negative, line quantity must be above zero, picked quantity cannot be negative, request quantity must be above zero, a job cannot list the same product twice) are enforced in the database as well as in the API. Money columns (`unit_cost`, `order_cost`, `holding_cost`) are `DECIMAL(10,2)`.

![ER diagram](docs/er_diagram.png)

* **Migrations:** `migrations/` (Flask-Migrate). `python -m flask --app app db upgrade` builds the schema.
* **MySQL script:** `schema.sql`, generated from the models by `python make_schema.py` so it cannot drift from the code. To use it without Flask: `mysql -u stockflow -p stockflow < schema.sql`.
* **Seed:** `seed.py` loads 8 stock items, 9 jobs with 27 BOM lines and the 4 demo users.
* **Indexes** for the real read patterns: `jobs(status, start_date)` for the queue, `stock_movements(product_id, created_at)` for the ledger, and a unique index on `products(sku)`.

### Rollback and backups

* **Undo the last migration:** `python -m flask --app app db downgrade`
* **Back up MySQL:** `mysqldump -u stockflow -p stockflow > backup.sql`. Restore with `mysql -u stockflow -p stockflow < backup.sql`.
* **Back up SQLite:** stop the app and copy `stockflow.db`. To restore, copy it back.

### Logging

The app writes to `logs/stockflow.log` (rotating file, so it cannot fill the disk) and to the console, with a level, time and message on each line. Unexpected errors are logged with a full traceback, and the database session is rolled back; the user only sees a clean JSON error.

---

## API

JSON over HTTP, under `/api`. Log in with `POST /api/auth/login`; a session cookie is then sent by the browser (Flask-Login). Lists are paginated with `?page=1&per_page=10` (maximum 100).

| Method | Endpoint | Who | What it does |
|---|---|---|---|
| POST | `/api/auth/login` | anyone | Log in |
| POST | `/api/auth/logout` | logged in | Log out |
| GET | `/api/auth/me` | logged in | Current user |
| GET | `/api/inventory` | reception, storeroom, operator | Stock with reserved, available, reorder point, suggested order and status. Filters: `status`, `search` |
| GET | `/api/jobs` | reception, storeroom, operator | Job list. Filters: `status`, `open=1`, `search` |
| GET | `/api/jobs/<job_number>` | reception, storeroom, operator | One job with BOM lines and shortages |
| POST | `/api/jobs` | reception | Open a job and soft-reserve its stock (201) |
| PATCH | `/api/jobs/<job_number>` | reception | Change start date, priority, customer or description. Reservations are re-checked. An issued job cannot be changed (409) |
| GET | `/api/queue?days=7` | storeroom, reception | Jobs starting in the window, with order-by alerts (1 to 30 days) |
| POST | `/api/picks` | operator, storeroom | Confirm a pick. Writes the ledger and updates the job (201) |
| POST | `/api/requests` | operator, storeroom | Ask the storeroom for extra material (201) |
| GET | `/api/requests` | storeroom | List material requests. Filter: `status` |
| PATCH | `/api/requests/<id>` | storeroom | Set a request to `open` or `done` |
| GET | `/api/kpis` | reception, storeroom, operator | Dashboard numbers |

The admin role may use every endpoint. The full request and response shapes are in `docs/openapi.json`, and a test checks that the file matches the real routes.

**Validation and errors.** Missing or invalid input is refused with a message for each field: **422** for a bad request body and **400** for a bad query parameter. Other codes: 401 not logged in, 403 wrong role, 404 not found, 409 conflict (for example picking more than the job needs). A duplicate product in a job is a 422, not a server error. Every error has the same shape:

```json
{"error": {"code": 422, "message": "Please fix the problems below.", "details": {"qty": "Quantity must be a whole number of 1 or more."}}}
```

## How the supply chain model is used

* **Soft reservation.** Reserved stock is what open jobs still need (`qty - picked`). Jobs are served in start-date order, so an earlier job can push a later one into shortage, and moving a job's start date re-checks every reservation.
* **Reorder point** = demand x lead time + safety stock (95 % service level).
* **Suggested order** = EOQ rounded up to the supplier minimum and pack size, and never less than the shortage itself.
* **Order-by date** = job start date minus lead time. If that date has already passed, the alert says **Expedite now**.

## Project structure

```
app.py                  main file: creates the app and starts it
config.py               development, testing and production settings
seed.py                 demo data
make_schema.py          generates schema.sql from the models
schema.sql              MySQL schema
requirements.txt        Python packages
.env.example            template for your .env
app/
  __init__.py           create_app() application factory
  blueprints/           routes: one file per group of endpoints
  models/               database tables
  schemas/              input checks
  services/             business logic that calls models/stock_model.py
  templates/            Jinja2 pages (thin shells)
  api_docs.py           serves the OpenAPI file and Swagger page
  errors.py, utils.py, extensions.py, logging_setup.py
models/stock_model.py   standalone supply chain model
migrations/             Flask-Migrate
static/                 CSS and page scripts (vanilla JS, fetch)
tests/                  pytest suites
docs/                   ER diagram, OpenAPI file, screenshots
dist/                   semester front-end prototype (static site, unchanged)
```

**Compared with the class sample project.** The class sample keeps routes, SQL and the connection in three files (`app.py`, `models.py`, `db.py`). We keep the same separation (routes never contain SQL, models never touch HTML) but split it by feature using Flask blueprints, which suits a larger application: routes in `app/blueprints/`, tables in `app/models/`, business rules in `app/services/`. The class layout's `app.py`, `requirements.txt`, `.env.example`, `schema.sql`, `templates/` and `static/` all exist here too; the templates sit in `app/templates/` because Flask looks for them next to the application package.

`dist/`, `templates/`, `render.py` and `sample_data.py` are the **semester prototype** (a static Bootstrap build with sample data). The Flask application in `app/` is the final project.

## Limitations

* **Automated tests run on SQLite.** The application itself was run and checked against MySQL 8 (migrations, seed data and the three flows), but the pytest suite uses an in-memory SQLite database.
* **The camera scan is simulated.** The scanner page offers the next BOM line or accepts a typed code. A real barcode reader would plug into the same function.
* **Demo data.** BOMs, customers and jobs are fictional. The company did not allow us to use its data.
* **No goods receipt.** The app plans and issues material but does not record deliveries or stock-count corrections.
* **Not deployed.** Running it in production would use a real WSGI server (for example Gunicorn behind Nginx), a strong `SECRET_KEY` and a production MySQL server. That setup was not part of this submission.
* **Bootstrap needs internet** because it loads from a CDN.

## Report

See the separate Extended Final Project Report submitted with this project.