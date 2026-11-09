import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(app):
    """Write logs to logs/stockflow.log (keeps 5 old files of 100 KB each)."""
    if app.testing:
        return
    log_dir = Path(app.root_path).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    handler = RotatingFileHandler(log_dir / "stockflow.log",
                                  maxBytes=100_000, backupCount=5)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s"))
    handler.setLevel(logging.INFO)

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("StockFlow started")