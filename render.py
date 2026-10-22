"""Build the website pages.

Combines the templates in /templates with the demo data from sample_data.py
and writes finished HTML files into a folder called "dist".

Run it with:   python render.py
Then open dist/index.html in your browser.
"""
from pathlib import Path
import shutil

from jinja2 import Environment, FileSystemLoader

import sample_data as data

HERE = Path(__file__).parent
DIST = HERE / "dist"

# page name -> template file
PAGES = {
    "dashboard": "dashboard.html",
    "job_files": "job_files.html",
    "queue": "queue.html",
    "inventory": "inventory.html",
    "scanner": "scanner.html",
}

# The menu: (page name, label, icon name)
NAV_ITEMS = [
    ("dashboard", "Dashboard", "house-door"),
    ("job_files", "Job files", "journal-text"),
    ("queue", "Storeroom queue", "clock-history"),
    ("inventory", "Inventory", "boxes"),
    ("scanner", "Shop-floor scanner", "upc-scan"),
]


def url_for(name, filename=None):
    """Stand-in for Flask's url_for.

    url_for('static', filename='css/style.css') -> static/css/style.css
    url_for('queue')                            -> queue.html
    """
    if name == "static":
        return "static/" + filename
    return name + ".html"


def main():
    env = Environment(loader=FileSystemLoader(HERE / "templates"), autoescape=True)
    env.globals["url_for"] = url_for

    # Everything the templates are allowed to use.
    values = {
        "today": data.TODAY,
        "jobs": data.JOBS,
        "inventory": data.INVENTORY,
        "kpis": data.kpis(),
        "payload": data.js_payload(),
        "nav_items": NAV_ITEMS,
    }

    # Start with a clean dist folder and copy the CSS/JS into it.
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(HERE / "static", DIST / "static")

    # Turn each template into a finished page.
    for name, template_file in PAGES.items():
        html = env.get_template(template_file).render(**values)
        (DIST / (name + ".html")).write_text(html, encoding="utf-8")

    # index.html just sends the browser on to the dashboard.
    redirect = ('<!doctype html><meta charset="utf-8">'
                '<meta http-equiv="refresh" content="0; url=dashboard.html">'
                '<a href="dashboard.html">Open StockFlow</a>')
    (DIST / "index.html").write_text(redirect, encoding="utf-8")

    print("Built " + str(len(PAGES)) + " pages in " + str(DIST))


if __name__ == "__main__":
    main()