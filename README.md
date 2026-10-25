# StockFlow Engine

**BFB 321 Semester Project – Group 19**

StockFlow Engine is a web application prototype for Penbro Kelnick (Pty) Ltd,
a South African manufacturer of custom transformers, power supplies and sheet
metal enclosures. It closes the communication gap between reception, where job
files are opened, and the storeroom, which currently hears about material needs
only the afternoon before assembly. When a job file is opened, its Bill of
Materials is checked against stock and soft-reserved, so shortages are
visible days in advance.

## Group members

| Name | Student number |
|------|----------------|
| Heinrich Willem Fourie | u23621452 |
| Tiaan Behr | u22710443 |

## What this submission contains

This repository covers the semester project:

- **Frontend (HTML, CSS, Bootstrap):** five responsive, accessible pages
  with form validation, sortable tables, search and filters.
  - Dashboard
  - Job files (new job form with Bill of Materials)
  - Storeroom queue (7 and 14 day look-ahead)
  - Inventory
  - Shop-floor scanner (mobile layout)
- **Supply chain model (Python):** `models/stock_model.py`, a standalone
  module with no Flask or database code. It provides:
  - EOQ, orders per year and total annual cost
  - safety stock and reorder point
  - shortage checking and soft reservation against a job's Bill of Materials
  - the planning-window filter and inventory record accuracy
- **Unit tests:** `tests/test_stock_model.py` checks the model against
  hand-calculated results.

## Live version

PASTE YOUR GITHUB PAGES LINK HERE

## Project structure

```
models/          supply chain calculations (independent of Flask)
tests/           unit tests for the model
templates/       Jinja2 HTML pages
static/          CSS and JavaScript
sample_data.py   demo data, calculated with the model
render.py        builds the pages into the docs/ folder
docs/            the built website (served by GitHub Pages)
```

## Setup and running

Requires Python 3.10 or newer and an internet connection (Bootstrap is loaded
from a CDN).

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Run the unit tests (24 should pass):

   ```
   python -m pytest
   ```

3. Build the pages:

   ```
   python render.py
   ```

4. Open `docs/index.html` in a web browser.

## Notes

- The data on screen is fictional demo data, and nothing is saved between page
  loads yet.
- The numbers shown (shortages, reorder points, suggested order quantities)
  are calculated by `models/stock_model.py`.# BFB321_Group19