import sqlite3
from typing import Any

# Launch GUI after initialization
from screen import run_app
from menu import load_menu


def init_database(db_path: str = "gourmet.db") -> None:
    """Ensure required database tables exist.

    Creates the `customer` and `custorder` tables if they do not already
    exist. This function performs only DDL and does not modify application
    data beyond ensuring the schema is present.

    Errors are handled silently (no raises, no prints) so callers can proceed
    or report errors via their own UI logic.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # customer table stores registered users
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS customer (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                mobilehp TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )

        # custorder table stores individual ordered items (one row per item)
        # orders table represents an order lifecycle (one order per customer)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES customer(user_id)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS custorder (
                order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                user_id INTEGER NOT NULL,
                menu_cat TEXT,
                menu_item TEXT,
                quantity INTEGER,
                item_total REAL,
                FOREIGN KEY(user_id) REFERENCES customer(user_id),
                FOREIGN KEY(order_id) REFERENCES orders(order_id)
            )
            """
        )

        conn.commit()
    finally:
        if conn is not None:
            conn.close()


def main(db_path: str = "gourmet.db") -> None:
    """Program entry point.

    Responsibilities performed here:
    - Initialize database schema if missing (calls `init_database`).

    Note: This function does not return any value and does not load the
    menu. The GUI or higher-level launcher should call `menu.load_menu()`
    (or a cached loader) and pass the resulting structure to components
    that need it.
    """
    init_database(db_path)
    # load menu once and launch the GUI
    menu_data = load_menu()
    run_app(menu_data=menu_data)


if __name__ == "__main__":
    # When run directly, initialize DB once.
    # GUI from here; the returned menu_data would be passed to a GUI launcher.
    main()
