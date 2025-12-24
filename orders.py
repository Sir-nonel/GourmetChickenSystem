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
            "INSERT INTO custorder (user_id, menu_cat, menu_item, quantity, item_total) VALUES (?, ?, ?, ?, ?)",
            (user_id, menu_cat, menu_item, quantity, item_total),
        )
        conn.commit()
    except sqlite3.Error:
        return
    finally:
        conn.close()


def create_order_for_user(user_id: int) -> Optional[int]:
    """Create a new order for the given user with status 'preparing'.

    Returns the new `order_id` on success or `None` on failure.
    """
    conn = get_connection()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO orders (user_id, status) VALUES (?, 'preparing')",
            (user_id,),
        )
        conn.commit()
        return int(cur.lastrowid)
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def assign_cart_items_to_order(user_id: int, order_id: int) -> None:
    """Assign any cart items (custorder rows) for `user_id` that are not
    yet assigned to an order to the provided `order_id`.
    """
    conn = get_connection()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE custorder SET order_id = ? WHERE user_id = ? AND (order_id IS NULL OR order_id = 0)",
            (order_id, user_id),
        )
        conn.commit()
    except sqlite3.Error:
        return
    finally:
        conn.close()


def get_preparing_orders() -> List[Dict]:
    """Return list of orders currently in 'preparing' status.

    Each dict contains: order_id, user_id, created_at
    """
    conn = get_connection()
    if conn is None:
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT o.order_id, o.user_id, c.name, o.created_at FROM orders o JOIN customer c ON o.user_id = c.user_id WHERE o.status = 'preparing' ORDER BY o.created_at ASC"
        )
        rows = cur.fetchall()
        result: List[Dict] = []
        for row in rows:
            result.append({
                "order_id": int(row[0]),
                "user_id": int(row[1]),
                "customer_name": str(row[2]),
                "created_at": row[3],
            })
        return result
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def get_active_orders_for_user(user_id: int) -> List[Dict]:
    """
    Returns:
    [
      {
        "order_id": int,
        "status": str,
        "created_at": str
      }
    ]
    """
    conn = get_connection()
    if conn is None:
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT order_id, status, created_at FROM orders WHERE user_id = ? AND status IN ('preparing', 'ready') ORDER BY created_at DESC",
            (user_id,),
        )
        rows = cur.fetchall()
        result: List[Dict] = []
        for row in rows:
            result.append({
                "order_id": int(row[0]) if row[0] is not None else None,
                "status": row[1],
                "created_at": row[2],
            })
        return result
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def get_order_items(order_id: int) -> List[Dict]:
    """Return items for a given order_id: menu_item, quantity, item_total."""
    conn = get_connection()
    if conn is None:
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT menu_item, quantity, item_total FROM custorder WHERE order_id = ?",
            (order_id,),
        )
        rows = cur.fetchall()
        result: List[Dict] = []
        for row in rows:
            result.append({
                "menu_item": row[0],
                "quantity": int(row[1]) if row[1] is not None else 0,
                "item_total": float(row[2]) if row[2] is not None else 0.0,
            })
        return result
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def mark_order_ready(order_id: int) -> None:
    """Mark the order as ready."""
    conn = get_connection()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE orders SET status = 'ready' WHERE order_id = ?",
            (order_id,),
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
            "SELECT order_item_id, user_id, menu_cat, menu_item, quantity, item_total FROM custorder WHERE user_id = ? AND order_id IS NULL",
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
                    "quantity": int(row[4]) if row[4] is not None else 0,
                    "item_total": float(row[5]) if row[5] is not None else 0.0,
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
