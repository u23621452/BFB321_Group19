"""Writes schema.sql (MySQL) straight from the SQLAlchemy models,
so the file can never drift away from the code. Run: python make_schema.py"""
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import mysql

from app import create_app
from app.extensions import db


def build_sql():
    dialect = mysql.dialect()
    parts = [
        "-- StockFlow Engine: MySQL schema (generated from the models by make_schema.py)",
        "-- Usage:  CREATE DATABASE stockflow CHARACTER SET utf8mb4;  USE stockflow;  then run this file.",
        "",
    ]
    # sorted_tables puts parent tables before the tables that reference them
    for table in db.metadata.sorted_tables:
        parts.append(str(CreateTable(table).compile(dialect=dialect)).strip() + ";")
        for index in sorted(table.indexes, key=lambda i: i.name):
            parts.append(str(CreateIndex(index).compile(dialect=dialect)).strip() + ";")
        parts.append("")
    return "\n".join(parts)


if __name__ == "__main__":
    with create_app("testing").app_context():
        text = build_sql()
    with open("schema.sql", "w", encoding="utf-8") as handle:
        handle.write(text)
    print("Wrote schema.sql")