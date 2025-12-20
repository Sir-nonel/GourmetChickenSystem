from typing import Dict, Any, List


def load_sales(path: str = "sales.txt") -> Dict[str, Dict[str, float]]:
    """Load sales data from `path` into an in-memory dict.

    Return structure:
    {
        "Chicken Burger": {"quantity": 10, "revenue": 49.9},
        "Tea": {"quantity": 5, "revenue": 9.95},
    }
    """
    sales: Dict[str, Dict[str, float]] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                # split from the right to allow '|' in item_name
                parts = line.rsplit("|", 2)
                if len(parts) != 3:
                    continue
                item_name, qty_s, rev_s = parts
                try:
                    quantity = int(qty_s)
                    revenue = float(rev_s)
                except (ValueError, TypeError):
                    continue
                sales[item_name] = {"quantity": quantity, "revenue": revenue}
    except FileNotFoundError:
        # no sales yet; return empty dict
        return {}
    except OSError:
        return {}
    return sales


def update_sales(sales_data: Dict[str, Dict[str, float]], item_name: str,
                 quantity: int, item_total: float) -> None:
    """Update `sales_data` for a single sold item.

    Parameters:
    - sales_data: the in-memory sales dict returned by `load_sales`
    - item_name: menu item name to update
    - quantity: number of units sold in this update
    - item_total: total revenue for these units (quantity * unit_price)

    Behavior:
    - Add a new entry if `item_name` is not present
    - Increment `quantity` and `revenue` for the item
    """
    if sales_data is None:
        return
    if not isinstance(quantity, int):
        try:
            quantity = int(quantity)
        except Exception:
            return
    try:
        item_total = float(item_total)
    except Exception:
        return

    # normalize item_name to avoid breaking the file format
    key = item_name.replace("|", " ").strip()
    if key in sales_data:
        try:
            sales_data[key]["quantity"] = int(sales_data[key].get("quantity", 0)) + quantity
            sales_data[key]["revenue"] = float(sales_data[key].get("revenue", 0.0)) + item_total
        except Exception:
            return
    else:
        sales_data[key] = {"quantity": int(quantity), "revenue": float(item_total)}


def save_sales(sales_data: Dict[str, Dict[str, float]], path: str = "sales.txt") -> None:
    """Persist `sales_data` to `path`.

        Writes `sales_data` to `path`, one line per item using the format:
        `item_name|quantity|revenue`.

        - `sales_data` is expected to be a dict mapping item_name -> dict with
            keys `quantity` (int) and `revenue` (float).
        - Function performs file I/O and overwrites the target file.
        - On file errors (OSError) the function returns without raising.
        """
    if sales_data is None:
        return
    try:
        with open(path, "w", encoding="utf-8") as f:
            for item_name, data in sales_data.items():
                try:
                    qty = int(data.get("quantity", 0))
                    rev = float(data.get("revenue", 0.0))
                except Exception:
                    continue
                # write as: item_name|quantity|revenue
                # ensure item_name does not contain pipe or newline
                name = item_name.replace("|", " ").replace("\n", " ")
                f.write(f"{name}|{qty}|{rev}\n")
    except OSError:
        return


def get_sales_summary(sales_data: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
    """Return a list-of-dicts summary suitable for display layers.

    Example return value:
    [
      {"item_name": "Chicken Burger", "quantity": 10, "revenue": 49.9},
      {"item_name": "Tea", "quantity": 5, "revenue": 9.95},
    ]

    This is a pure transformation of `sales_data` and does not perform I/O.
    """
    if not sales_data:
        return []
    result: List[Dict[str, Any]] = []
    try:
        for item_name, data in sales_data.items():
            qty = int(data.get("quantity", 0))
            rev = float(data.get("revenue", 0.0))
            result.append({"item_name": item_name, "quantity": qty, "revenue": rev})
    except Exception:
        return []
    return result
