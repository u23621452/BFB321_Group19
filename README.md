# StockFlow Engine

A web application for **Penbro Kelnick (Pty) Ltd**, a South African manufacturer of industrial transformers, power supplies and sheet-metal enclosures. StockFlow connects the three places where a work order lives (reception, the storeroom and the shop floor) so that material shortages are seen days before assembly instead of the afternoon before.

Built for **BFB 321** (University of Pretoria), group **BFB321_Group19**.

| Member | Student number |

| Heinrich Willem Fourie | u23621452 |
| Tiaan Behr | u22710443 |
| Full Name Here | uXXXXXXXX |

> **About the data.** We asked Penbro Kelnick for access to real storeroom data and were told we could not use it. All stock items, jobs, customers and BOMs in this project are therefore **fictional demo data**, modelled on the kind of items a storeroom like theirs holds. No company data is used anywhere in this repository.

---

## What it does

| Role | What they do in the app |

| **Reception** | Opens a job file with its Bill of Materials. Stock is *soft-reserved* immediately and any shortage is flagged. |
| **Storeroom** | Sees a 7- or 14-day queue of upcoming jobs, with shortage alerts, an **order-by date** (start date minus supplier lead time) and a suggested order quantity from the supply chain model. |
| **Operator** | Uses a phone-friendly scanner page to confirm picks. Every pick writes a row to the stock ledger and updates the job. They can also request extra material. |
| **Admin** | Can use everything. |

The supply chain logic (EOQ, safety stock at a 95 % service level, reorder point, soft reservation, lookahead) lives in `models/stock_model.py`. It is plain Python with no Flask or database imports, and it has its own unit tests. The API calls it from `app/services/`.

## The three end-to-end flows

**1. Reception opens a job and stock is reserved**
![Flow 1](docs/screenshots/flow1.gif)

**2. Storeroom sees the shortage in the queue, with an order-by date**
![Flow 2](docs/screenshots/flow2.gif)

**3. Operator confirms a pick on the shop floor and the ledger updates** (phone width; the second pick is refused because it is more than the job needs)
![Flow 3](docs/screenshots/flow3.gif)

The flows are connected. A job created by reception appears in the storeroom's queue and on the operator's scanner, and a pick changes the inventory page and the dashboard numbers.

### Screenshots

| ![Login](docs/screenshots/01-login.png) | ![Dashboard](docs/screenshots/02-dashboard.png) |
| Login, with demo accounts | Dashboard KPIs |
| ![Job file created](docs/screenshots/03-flow1-job-file-created.png) | ![Job detail](docs/screenshots/04-job-detail.png) |
| Job file created, shortage reported | Job detail with BOM lines |
| ![Queue 7 days](docs/screenshots/05-flow2-storeroom-queue.png) | ![Queue 14 days](docs/screenshots/06-queue-14-days.png) |
| Storeroom queue, next 7 days | Next 14 days |
| ![Inventory](docs/screenshots/07-inventory.png) | ![API docs](docs/screenshots/14-api-docs.png) |
| Inventory with reservations | Swagger page for the API |

### Loading, empty and error states

Every list and form handles the three states a user can meet:

| Loading | Empty | Error (with retry) |

| ![Loading](docs/screenshots/10-state-loading.png) | ![Empty](docs/screenshots/08-state-empty.png) | ![Error](docs/screenshots/09-state-error.png) |

Phone view of the scanner:

| Scanner | Pick panel | After confirming |

| ![Scanner](docs/screenshots/11-flow3-scanner.png) | ![Pick](docs/screenshots/12-scanner-pick.png) | ![Picked](docs/screenshots/13-scanner-picked.png) |

---

## Quick start (runbook)

You need **Python 3.11 or newer**. These are the exact commands for Windows PowerShell; on macOS or Linux use `python3` and the same arguments.

```powershell
# 1. Install the packages
python -m pip install -r requirements.txt

# 2. Create your settings file (works as-is for local use)
copy .env.example .env

# 3. Create the database tables from the migrations
python -m flask --app run db upgrade

# 4. Fill the database with demo data
python seed.py

# 5. Start the app
python run.py
```

Open **http://127.0.0.1:5000** and log in with a demo account (password `Password123` for all):

| Account | Role |

| `reception@stockflow.test` | opens job files |
| `storeroom@stockflow.test` | plans the queue |
| `operator@stockflow.test` | shop-floor picks |
| `admin@stockflow.test` | everything |

The page styles come from a CDN (Bootstrap), so the browser needs an internet connection.

**API documentation:** http://127.0.0.1:5000/api/docs (Swagger page) and `docs/openapi.json` (the OpenAPI 3 file).

### Resetting the demo

`python seed.py` empties the tables and loads the demo data again. Job start dates are set **relative to the day you run it**, so run it again on demo day to keep the queue full.

### Running the tests

```powershell
python -m pytest
```

There are **93 tests**: supply chain model unit tests, API tests for every endpoint, page-access tests, and integration tests that walk through each flow (`tests/test_flows.py`). They run on an in-memory SQLite database, so they never touch your real data.

---

## Configuration

Settings come from `config.py` (development, testing and production classes) and from a `.env` file. `.env.example` lists every setting and contains no secrets. The real `.env` is never committed.

| Setting | Meaning |

| `APP_ENV` | `development`, `testing` or `production` |
| `SECRET_KEY` | Signs the login session cookie. Use a long random value in production. |
| `DATABASE_URL` | SQLite by default (`sqlite:///stockflow.db`). For MySQL: `mysql+pymysql://user:password@localhost/stockflow` |

## Database

Six tables, with `created_at` and `updated_at` on each. Foreign keys, unique keys and check constraints (stock on hand cannot be negative, line quantity must be above zero, a job cannot list the same product twice) are enforced in the database as well as in the API.

![ER diagram](docs/er_diagram.png)

* **Migrations:** `migrations/` (Flask-Migrate). `python -m flask --app run db upgrade` builds the schema.
* **MySQL script:** `schema.sql`, generated from the models by `python make_schema.py` so it cannot drift from the code.
* **Seed:** `seed.py` loads 8 stock items, 9 jobs with 27 BOM lines and the 4 demo users.
* **Indexes** for the real read patterns: `jobs(status, start_date)` for the queue, `stock_movements(product_id, created_at)` for the ledger, and a unique index on `products(sku)`.

### Rollback and backups

* **Undo the last migration:** `python -m flask --app run db downgrade`
* **Back up SQLite:** stop the app and copy `stockflow.db`. To restore, copy it back.
* **Back up MySQL:** `mysqldump -u user -p stockflow > backup.sql`. Restore with `mysql -u user -p stockflow < backup.sql`.

### Logging

The app writes to `logs/stockflow.log` (rotating file, so it cannot fill the disk) and to the console. Unexpected errors are logged with a full traceback; the user only sees a clean JSON error.

---

## API

JSON over HTTP, under `/api`. Log in with `POST /api/auth/login`; a session cookie is then sent by the browser (Flask-Login). Lists are paginated with `?page=1&per_page=10` (maximum 100).

| Method | Endpoint | Who | What it does |

| POST | `/api/auth/login` | anyone | Log in |
| POST | `/api/auth/logout` | logged in | Log out |
| GET | `/api/auth/me` | logged in | Current user |
| GET | `/api/inventory` | reception, storeroom, operator | Stock with reserved, available, reorder point, suggested order and status. Filters: `status`, `search` |
| GET | `/api/jobs` | reception, storeroom, operator | Job list. Filters: `status`, `open=1`, `search` |
| GET | `/api/jobs/<job_number>` | reception, storeroom, operator | One job with BOM lines and shortages |
| POST | `/api/jobs` | reception | Open a job and soft-reserve its stock |
| GET | `/api/queue?days=7` | storeroom, reception | Jobs starting in the window, with order-by alerts (1 to 30 days) |
| POST | `/api/picks` | operator, storeroom | Confirm a pick. Writes the ledger and updates the job |
| POST | `/api/requests` | operator, storeroom | Ask the storeroom for extra material |
| GET | `/api/requests` | storeroom | List material requests. Filter: `status` |
| GET | `/api/kpis` | reception, storeroom, operator | Dashboard numbers |

The admin role may use every endpoint. The full request and response shapes are in `docs/openapi.json`, and a test checks that the file matches the real routes.

**Validation and errors.** Bad input returns **422** with a message for each field. Other codes: 400 bad query, 401 not logged in, 403 wrong role, 404 not found, 409 conflict (for example picking more than the job needs). Every error has the same shape:

```json
{"error": {"code": 422, "message": "Please fix the problems below.", "details": {"qty": "Quantity must be a whole number of 1 or more."}}}
```

## How the supply chain model is used

* **Soft reservation.** Reserved stock is what open jobs still need (`qty - picked`). Jobs are served in start-date order, so an earlier job can push a later one into shortage.
* **Reorder point** = demand x lead time + safety stock (95 % service level).
* **Suggested order** = EOQ rounded up to the supplier minimum and pack size, and never less than the shortage itself.
* **Order-by date** = job start date minus lead time. If that date has already passed, the alert says **Expedite now**.

## Project structure

```
app/
  __init__.py        create_app() application factory
  blueprints/        one file per group of endpoints
  models/            database tables
  schemas/           input checks
  services/          business logic that calls models/stock_model.py
  templates/         Jinja2 pages (thin shells)
  api_docs.py        serves the OpenAPI file and Swagger page
models/stock_model.py   standalone supply chain model
migrations/         Flask-Migrate
static/js/          page scripts (vanilla JS, fetch)
tests/              pytest suites
docs/               ER diagram, OpenAPI file, screenshots
dist/               semester front-end prototype (static site, unchanged)
config.py  seed.py  run.py  schema.sql  .env.example
```

`dist/`, `templates/`, `render.py` and `sample_data.py` are the **semester prototype** (a static Bootstrap build with sample data). The Flask application in `app/` is the final project.

## Limitations

* **SQLite is the development database.** The code and `schema.sql` are written to be MySQL-ready (change `DATABASE_URL`), but all testing was done on SQLite.
* **The camera scan is simulated.** The scanner page offers the next BOM line or accepts a typed code. A real barcode reader would plug into the same function.
* **Demo data only.** The company declined data access, so every figure in the app is fictional. Impact figures in the report are projections, not measurements from a live site.
* **Not deployed.** Running it in production would use a real WSGI server (for example Gunicorn behind Nginx), a strong `SECRET_KEY` and a MySQL `DATABASE_URL`. That setup was not part of this submission.
* **Bootstrap needs internet** because it loads from a CDN.