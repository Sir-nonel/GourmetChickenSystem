import sqlite3
from typing import List, Dict, Optional


def get_connection(db_path: str = "gourmet.db") -> Optional[sqlite3.Connection]:
    """Open and return a sqlite3 connection to `db_path`.

    Returns the connection on success or `None` if a connection cannot be
    established. Caller is responsible for closing the connection when done.
    """
    try:
        return sqlite3.connect(db_path)
    except sqlite3.Error:
        return None


def add_order_item(user_id: int, menu_cat: str, menu_item: str, quantity: int,
                   item_total: float, status: str = "pending") -> None:
    """Insert a new order item row into the `custorder` table.

    This function does not raise. On DB errors it returns without effect.
    """
    conn = get_connection()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO custorder (user_id, menu_cat, menu_item, quantity, item_total, status) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, menu_cat, menu_item, quantity, item_total, status),
        )
        conn.commit()
    except sqlite3.Error:
        return
    finally:
        conn.close()


def get_pending_orders(user_id: int) -> List[Dict]:
    """Return a list of pending order items for the given user.

    Each returned dict has keys: order_item_id, user_id, menu_cat, menu_item,
    quantity, item_total, status. Returns an empty list on error or if none.
    """
    conn = get_connection()
    if conn is None:
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT order_item_id, user_id, menu_cat, menu_item, quantity, item_total, status FROM custorder WHERE user_id = ? AND status = 'pending'",
            (user_id,),
        )
        rows = cur.fetchall()
        result: List[Dict] = []
        for row in rows:
            result.append(
                {
                    "order_item_id": int(row[0]),
                    "user_id": int(row[1]),
                    "menu_cat": row[2],
                    "menu_item": row[3],
                    "quantity": int(row[4]),
                    "item_total": float(row[5]),
                    "status": row[6],
                }
            )
        return result
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def update_order_item(order_item_id: int, new_quantity: int, new_item_total: float) -> None:
    """Update quantity and item_total for a pending order item.

    Only updates rows with status 'pending'. Swallows DB errors.
    """
    conn = get_connection()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE custorder SET quantity = ?, item_total = ? WHERE order_item_id = ? AND status = 'pending'",
            (new_quantity, new_item_total, order_item_id),
        )
        conn.commit()
    except sqlite3.Error:
        return
    finally:
        conn.close()


def delete_order_item(order_item_id: int) -> None:
    """Delete a pending order item by its id.

    Only deletes rows with status 'pending'. Swallows DB errors.
    """
    conn = get_connection()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM custorder WHERE order_item_id = ? AND status = 'pending'",
            (order_item_id,),
        )
        conn.commit()
    except sqlite3.Error:
        return
    finally:
        conn.close()


def confirm_orders(user_id: int) -> None:
    """Mark all pending items for `user_id` as confirmed.

    Updates status from 'pending' to 'confirmed'. Swallows DB errors.
    """
    conn = get_connection()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE custorder SET status = 'confirmed' WHERE user_id = ? AND status = 'pending'",
            (user_id,),
        )
        conn.commit()
    except sqlite3.Error:
        return
    finally:
        conn.close()

