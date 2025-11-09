import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "data", "caf-e.db")
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

_connection: Optional[sqlite3.Connection] = None
_lock = threading.Lock()


def _get_connection() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(DB_FILE, check_same_thread=False)
        _connection.row_factory = sqlite3.Row
    return _connection


def init_db() -> None:
    """
    Initialize the SQLite database with the tables we need for orders and receipts.
    Safe to call multiple times; tables are created if they do not already exist.
    """
    with _lock:
        conn = _get_connection()
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE,
                customer_id TEXT,
                customer_name TEXT,
                customer_email TEXT,
                status TEXT,
                total REAL,
                currency TEXT,
                items_json TEXT NOT NULL,
                metadata_json TEXT,
                created_at TEXT NOT NULL,
                knot_tx_id TEXT,
                payment_status TEXT,
                loyalty_earned INTEGER DEFAULT 0,
                paid INTEGER DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id TEXT UNIQUE,
                order_id TEXT,
                session_id TEXT,
                total REAL,
                currency TEXT,
                line_items_json TEXT,
                raw_payload_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE
            )
            """
        )
        for column, definition in {
            "knot_tx_id": "TEXT",
            "payment_status": "TEXT",
            "loyalty_earned": "INTEGER DEFAULT 0",
            "paid": "INTEGER DEFAULT 0",
        }.items():
            try:
                conn.execute(f"ALTER TABLE orders ADD COLUMN {column} {definition}")
            except sqlite3.OperationalError:
                pass

        conn.commit()


def _serialize(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_order(order: Dict[str, Any]) -> None:
    """
    Persist an order payload. Expects keys:
        - order_id (str)
        - customer_id (optional str)
        - customer_name (optional str)
        - customer_email (optional str)
        - status (optional str)
        - total (optional float)
        - currency (optional str, defaults to 'USD')
        - items (Iterable[Dict])
        - metadata (optional Dict)
    """
    if "order_id" not in order:
        raise ValueError("order_id is required")
    if "items" not in order:
        raise ValueError("items is required")

    payload = {
        "order_id": order["order_id"],
        "customer_id": order.get("customer_id"),
        "customer_name": order.get("customer_name"),
        "customer_email": order.get("customer_email"),
        "status": order.get("status", "created"),
        "total": order.get("total"),
        "currency": order.get("currency", "USD"),
        "items_json": _serialize(order["items"]),
        "metadata_json": _serialize(order.get("metadata", {})),
        "created_at": order.get("created_at", _now_iso()),
        "knot_tx_id": order.get("knot_tx_id"),
        "payment_status": order.get("payment_status"),
        "loyalty_earned": order.get("loyalty_earned", 0),
        "paid": 1 if order.get("paid") else 0,
    }

    with _lock:
        conn = _get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO orders (
                order_id,
                customer_id,
                customer_name,
                customer_email,
                status,
                total,
                currency,
                items_json,
                metadata_json,
                created_at,
                knot_tx_id,
                payment_status,
                loyalty_earned,
                paid
            ) VALUES (
                :order_id,
                :customer_id,
                :customer_name,
                :customer_email,
                :status,
                :total,
                :currency,
                :items_json,
                :metadata_json,
                :created_at,
                :knot_tx_id,
                :payment_status,
                :loyalty_earned,
                :paid
            )
            """,
            payload,
        )
        conn.commit()


def save_receipt(receipt: Dict[str, Any]) -> None:
    """
    Persist a receipt payload. Expects keys:
        - receipt_id (str)
        - order_id (optional str)
        - session_id (optional str)
        - total (optional float)
        - currency (optional str, defaults to 'USD')
        - line_items (optional Iterable[Dict])
        - raw_payload (optional Dict)
    """
    if "receipt_id" not in receipt:
        raise ValueError("receipt_id is required")

    payload = {
        "receipt_id": receipt["receipt_id"],
        "order_id": receipt.get("order_id"),
        "session_id": receipt.get("session_id"),
        "total": receipt.get("total"),
        "currency": receipt.get("currency", "USD"),
        "line_items_json": _serialize(receipt.get("line_items", [])),
        "raw_payload_json": _serialize(receipt.get("raw_payload", {})),
        "created_at": receipt.get("created_at", _now_iso()),
    }

    with _lock:
        conn = _get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO receipts (
                receipt_id,
                order_id,
                session_id,
                total,
                currency,
                line_items_json,
                raw_payload_json,
                created_at
            ) VALUES (
                :receipt_id,
                :order_id,
                :session_id,
                :total,
                :currency,
                :line_items_json,
                :raw_payload_json,
                :created_at
            )
            """,
            payload,
        )
        conn.commit()


def get_orders(limit: Optional[int] = None) -> Iterable[Dict[str, Any]]:
    with _lock:
        conn = _get_connection()
        query = "SELECT * FROM orders ORDER BY datetime(created_at) DESC"
        if limit:
            query += " LIMIT ?"
            rows = conn.execute(query, (limit,)).fetchall()
        else:
            rows = conn.execute(query).fetchall()
    return [_row_to_dict(row) for row in rows]


def get_order(order_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        conn = _get_connection()
        row = conn.execute(
            "SELECT * FROM orders WHERE order_id = ?", (order_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def update_order(
    order_id: str,
    *,
    status: Optional[str] = None,
    total: Optional[float] = None,
    currency: Optional[str] = None,
    knot_tx_id: Optional[str] = None,
    payment_status: Optional[str] = None,
    loyalty_delta: Optional[int] = None,
    paid: Optional[bool] = None,
    metadata_updates: Optional[Dict[str, Any]] = None,
) -> None:
    with _lock:
        conn = _get_connection()
        row = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
        if row is None:
            raise ValueError(f"Order {order_id} not found")

        data = dict(row)
        updates: Dict[str, Any] = {}

        if status is not None:
            updates["status"] = status
        if total is not None:
            updates["total"] = total
        if currency is not None:
            updates["currency"] = currency
        if knot_tx_id is not None:
            updates["knot_tx_id"] = knot_tx_id
        if payment_status is not None:
            updates["payment_status"] = payment_status
        if paid is not None:
            updates["paid"] = 1 if paid else 0
        if loyalty_delta is not None:
            current_loyalty = data.get("loyalty_earned") or 0
            updates["loyalty_earned"] = current_loyalty + loyalty_delta

        if metadata_updates:
            existing_meta = json.loads(data.get("metadata_json") or "{}")
            existing_meta.update(metadata_updates)
            updates["metadata_json"] = _serialize(existing_meta)

        if not updates:
            return

        assignments = ", ".join(f"{key} = :{key}" for key in updates.keys())
        updates["order_id"] = order_id
        conn.execute(f"UPDATE orders SET {assignments} WHERE order_id = :order_id", updates)
        conn.commit()


def get_receipts(limit: Optional[int] = None, order_id: Optional[str] = None) -> Iterable[Dict[str, Any]]:
    with _lock:
        conn = _get_connection()
        query = "SELECT * FROM receipts"
        params: list[Any] = []
        filters = []
        if order_id:
            filters.append("order_id = ?")
            params.append(order_id)
        if filters:
            query += " WHERE " + " AND ".join(filters)
        query += " ORDER BY datetime(created_at) DESC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        rows = conn.execute(query, tuple(params)).fetchall()
    return [_row_to_dict(row) for row in rows]


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    data = dict(row)
    if "items_json" in data and data["items_json"]:
        data["items"] = json.loads(data["items_json"])
    if "metadata_json" in data and data["metadata_json"]:
        data["metadata"] = json.loads(data["metadata_json"])
    if "line_items_json" in data and data["line_items_json"]:
        data["line_items"] = json.loads(data["line_items_json"])
    if "raw_payload_json" in data and data["raw_payload_json"]:
        data["raw_payload"] = json.loads(data["raw_payload_json"])
    data.pop("items_json", None)
    data.pop("metadata_json", None)
    data.pop("line_items_json", None)
    data.pop("raw_payload_json", None)
    return data


def reset_connection() -> None:
    global _connection
    with _lock:
        if _connection is not None:
            _connection.close()
            _connection = None


