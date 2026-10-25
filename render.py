
from pathlib import Path
import shutil
import stat

from jinja2 import Environment, FileSystemLoader

import sample_data as data

HERE = Path(__file__).parent
DIST = HERE / "docs"

PAGES = {
    "dashboard": "dashboard.html",
    "job_files": "job_files.html",
    "queue": "queue.html",
    "inventory": "inventory.html",
    "scanner": "scanner.html",
}

NAV_ITEMS = [
    ("dashboard", "Dashboard", "house-door"),
    ("job_files", "Job files", "journal-text"),
    ("queue", "Storeroom queue", "clock-history"),
    ("inventory", "Inventory", "boxes"),
    ("scanner", "Shop-floor scanner", "upc-scan"),
]


def url_for(name, filename=None):
    if name == "static":
        return "static/" + filename
    return name + ".html"


def main():
    env = Environment(
        loader=FileSystemLoader(HERE / "templates"),
        autoescape=True
    )
    env.globals["url_for"] = url_for

    values = {
        "today": data.TODAY,
        "jobs": data.JOBS,
        "inventory": data.INVENTORY,
        "kpis": data.kpis(),
        "payload": data.js_payload(),
        "nav_items": NAV_ITEMS,
    }

    DIST.mkdir(exist_ok=True)

    static_source = HERE / "static"
    static_dest = DIST / "static"
    static_dest.mkdir(parents=True, exist_ok=True)

    for source in static_source.rglob("*"):
        try:
            attributes = getattr(
                source.stat(follow_symlinks=False),
                "st_file_attributes",
                0
            )

            is_reparse_point = bool(
                attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            )

            if source.is_symlink() or is_reparse_point:
                continue

            relative = source.relative_to(static_source)
            destination = static_dest / relative

            if source.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            elif source.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)

        except PermissionError as exc:
            print(f"Skipping inaccessible item {source}: {exc}")

    for name, template_file in PAGES.items():
        html = env.get_template(template_file).render(**values)
        (DIST / (name + ".html")).write_text(
            html,
            encoding="utf-8"
        )

    redirect = (
        '<!doctype html><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0; url=dashboard.html">'
        '<a href="dashboard.html">Open StockFlow</a>'
    )

    (DIST / "index.html").write_text(
        redirect,
        encoding="utf-8"
    )

    print(f"Built {len(PAGES)} pages in {DIST}")


if __name__ == "__main__":
    main()
