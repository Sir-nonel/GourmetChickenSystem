import sqlite3
import sales as sales_mod
from typing import List, Dict, Optional


def get_connection(db_path: str = "gourmet.db") -> Optional[sqlite3.Connection]:
    """Return a sqlite3 connection to the application's database file or None."""
    try:
        return sqlite3.connect(db_path)
    except sqlite3.Error:
        return None


def add_order_item(user_id: int, menu_cat: str, menu_item: str, quantity: int,
                   item_total: float, status: str = "pending") -> None:
    """Add an item to the user's cart, merging with an existing cart row if present."""
    conn = get_connection()
    if conn is None:
        return
    try:
        cur = conn.cursor()

        # check if item already exists in the user's cart (order_id IS NULL)
        cur.execute(
            """
            SELECT order_item_id, quantity, item_total
            FROM custorder
            WHERE user_id = ?
              AND menu_cat = ?
              AND menu_item = ?
              AND order_id IS NULL
            """,
            (user_id, menu_cat, menu_item),
        )
        row = cur.fetchone()

        if row:
            order_item_id, old_qty, old_total = row
            try:
                new_qty = int(old_qty) + int(quantity)
            except Exception:
                new_qty = quantity
            try:
                new_total = float(old_total) + float(item_total)
            except Exception:
                new_total = item_total

            cur.execute(
                """
                UPDATE custorder
                SET quantity = ?, item_total = ?
                WHERE order_item_id = ?
                """,
                (new_qty, new_total, order_item_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO custorder
                (user_id, menu_cat, menu_item, quantity, item_total)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, menu_cat, menu_item, quantity, item_total),
            )

        conn.commit()
    except sqlite3.Error:
        return
    finally:
        conn.close()


def create_order_for_user(user_id: int) -> Optional[int]:
    """Create a new order header for the user with status 'preparing'."""
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
    """Attach the user's unassigned cart items to the specified order id."""
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
    """Return a list of orders currently marked as preparing along with metadata."""
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
    """Return recent orders for a user including preparing and ready statuses."""
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
    """Return the line items for the given order id including quantities and totals."""
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
    """Set the order status to 'ready' and attempt to record sales for it."""
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
        # record sales for completed order: update sales.txt via sales module
        try:
            items = get_order_items(order_id)
            sales_data = sales_mod.load_sales()
            for it in items:
                name = it.get("menu_item", "")
                qty = int(it.get("quantity", 0) or 0)
                item_total = float(it.get("item_total", 0.0) or 0.0)
                if qty > 0 and item_total >= 0:
                    sales_mod.update_sales(sales_data, name, qty, item_total)
            sales_mod.save_sales(sales_data)
        except Exception:
            # do not let sales logging break the order status update
            pass
    except sqlite3.Error:
        return
    finally:
        conn.close()


def delete_order(order_id: int) -> None:
    """Remove the order header and all associated custorder rows for an order."""
    conn = get_connection()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        # delete line items first
        cur.execute(
            "DELETE FROM custorder WHERE order_id = ?",
            (order_id,),
        )
        # then delete order header
        cur.execute(
            "DELETE FROM orders WHERE order_id = ?",
            (order_id,),
        )
        conn.commit()
    except sqlite3.Error:
        return
    finally:
        conn.close()


def get_pending_orders(user_id: int) -> List[Dict]:
    """Return the user's pending cart items that are not yet assigned to an order."""
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
    """Update quantity and item total for a cart row identified by order_item_id."""
    conn = get_connection()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE custorder SET quantity = ?, item_total = ? WHERE order_item_id = ?",
            (new_quantity, new_item_total, order_item_id),
        )
        conn.commit()
    except sqlite3.Error:
        return
    finally:
        conn.close()


def delete_order_item(order_item_id: int) -> None:
    """Delete a cart row identified by its order_item_id."""
    conn = get_connection()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM custorder WHERE order_item_id = ?",
            (order_item_id,),
        )
        conn.commit()
    except sqlite3.Error:
        return
    finally:
        conn.close()
