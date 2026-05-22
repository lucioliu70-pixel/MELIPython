from __future__ import annotations

import sqlite3
from contextlib import contextmanager


CREATE_ITEMS_SNAPSHOT = """
CREATE TABLE IF NOT EXISTS items_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT,
    keyword TEXT,
    item_id TEXT,
    title TEXT,
    price REAL,
    currency_id TEXT,
    sold_quantity INTEGER,
    available_quantity INTEGER,
    seller_id TEXT,
    seller_nickname TEXT,
    category_id TEXT,
    listing_type_id TEXT,
    free_shipping INTEGER,
    logistic_type TEXT,
    state_name TEXT,
    city_name TEXT,
    permalink TEXT,
    thumbnail TEXT,
    brand TEXT,
    model TEXT,
    attributes_json TEXT,
    date_collected TEXT
);
"""


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.execute(CREATE_ITEMS_SNAPSHOT)

    def insert_items_snapshot(self, rows: list[tuple]) -> None:
        sql = """
        INSERT INTO items_snapshot (
            batch_id, keyword, item_id, title, price, currency_id, sold_quantity, available_quantity,
            seller_id, seller_nickname, category_id, listing_type_id, free_shipping, logistic_type,
            state_name, city_name, permalink, thumbnail, brand, model, attributes_json, date_collected
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """
        with self.connect() as conn:
            conn.executemany(sql, rows)
