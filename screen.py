import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from typing import Dict, Any, Optional

import menu as menu_mod
import auth as auth_mod
import orders as orders_mod
import sales as sales_mod


class App(tk.Tk):
    def __init__(self, menu_data: Optional[Dict[str, Dict[str, float]]] = None):
        super().__init__()
        self.title("Gourmet Chicken System")
        self.geometry("500x550")

        # Global GUI state
        self.current_user_id: Optional[int] = None
        self.menu_data = menu_data or menu_mod.load_menu()

        container = tk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        self.frames: Dict[str, tk.Frame] = {}
        for F in (LoginFrame, RegisterFrame, MenuFrame, OrdersFrame, OwnerSalesFrame):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginFrame")

    def show_frame(self, name: str) -> None:
        frame = self.frames[name]
        if hasattr(frame, "on_show"):
            try:
                frame.on_show()
            except Exception:
                pass
        frame.tkraise()


class LoginFrame(tk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Login", font=(None, 18)).pack(pady=10)

        form = tk.Frame(self)
        form.pack(pady=10)

        tk.Label(form, text="Username").grid(row=0, column=0, sticky="e")
        self.username_entry = tk.Entry(form)
        self.username_entry.grid(row=0, column=1)

        tk.Label(form, text="Password").grid(row=1, column=0, sticky="e")
        self.password_entry = tk.Entry(form, show="*")
        self.password_entry.grid(row=1, column=1)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Login", command=self.do_login).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Register", command=lambda: controller.show_frame("RegisterFrame")).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Owner Sales", command=lambda: controller.show_frame("OwnerSalesFrame")).grid(row=0, column=2, padx=5)

    def do_login(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        user_id = auth_mod.login_user(username, password)
        if user_id is not None:
            self.controller.current_user_id = user_id
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.controller.show_frame("MenuFrame")
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")


class RegisterFrame(tk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Register", font=(None, 18)).pack(pady=10)

        form = tk.Frame(self)
        form.pack(pady=10)

        tk.Label(form, text="Name").grid(row=0, column=0, sticky="e")
        self.name_entry = tk.Entry(form)
        self.name_entry.grid(row=0, column=1)

        tk.Label(form, text="Username").grid(row=1, column=0, sticky="e")
        self.username_entry = tk.Entry(form)
        self.username_entry.grid(row=1, column=1)

        tk.Label(form, text="Password").grid(row=2, column=0, sticky="e")
        self.password_entry = tk.Entry(form, show="*")
        self.password_entry.grid(row=2, column=1)

        tk.Label(form, text="Mobile HP").grid(row=3, column=0, sticky="e")
        self.mobile_entry = tk.Entry(form)
        self.mobile_entry.grid(row=3, column=1)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Register", command=self.do_register).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Back", command=lambda: controller.show_frame("LoginFrame")).grid(row=0, column=1, padx=5)

    def do_register(self) -> None:
        name = self.name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        mobilehp = self.mobile_entry.get().strip()
        ok, msg = auth_mod.register_user(name, username, password, mobilehp)
        if ok:
            messagebox.showinfo("Registered", "Registration successful. Please log in.")
            self.name_entry.delete(0, tk.END)
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.mobile_entry.delete(0, tk.END)
            self.controller.show_frame("LoginFrame")
        else:
            messagebox.showerror("Registration Failed", msg)


class MenuFrame(tk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller

        top = tk.Frame(self)
        top.pack(fill=tk.X, pady=6)
        tk.Label(top, text="Menu", font=(None, 18)).pack(side=tk.LEFT, padx=10)
        tk.Button(top, text="My Orders", command=lambda: controller.show_frame("OrdersFrame")).pack(side=tk.RIGHT, padx=6)
        tk.Button(top, text="Logout", command=self.logout).pack(side=tk.RIGHT)

        self.canvas = tk.Frame(self)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Selection controls (single combobox + qty + add button)
        control = tk.Frame(self)
        control.pack(fill=tk.X, padx=10, pady=(6, 0))
        tk.Label(control, text="Select Item").grid(row=0, column=0, sticky="e")
        self.item_var = tk.StringVar()
        self.item_combo = ttk.Combobox(control, textvariable=self.item_var, state="readonly", width=40)
        self.item_combo.grid(row=0, column=1, padx=6)
        tk.Label(control, text="Quantity").grid(row=1, column=0, sticky="e")
        self.sel_qty_entry = tk.Entry(control, width=6)
        self.sel_qty_entry.insert(0, "1")
        self.sel_qty_entry.grid(row=1, column=1, sticky="w", padx=6)
        tk.Button(control, text="Add Selected", command=self.add_selected_item).grid(row=2, column=0, columnspan=2, pady=6)

        # no per-item qty entries; selection is via combobox + `self.sel_qty_entry`
        self.build_menu()
        self.populate_items()

    def build_menu(self) -> None:
        # Clear previous
        for child in self.canvas.winfo_children():
            child.destroy()

        menu_data = self.controller.menu_data
        for cat, items in menu_data.items():
            cat_label = tk.Label(self.canvas, text=cat, font=(None, 14, "bold"))
            cat_label.pack(anchor="w", padx=10, pady=(8, 0))
            for item_name, price in items.items():
                row = tk.Frame(self.canvas)
                row.pack(fill=tk.X, padx=20, pady=2)
                tk.Label(row, text=f"{item_name} (RM{price:.2f})").pack(side=tk.LEFT)
                # per-row quantity and add controls removed in favor of single combobox + Add button
        # refresh combobox values after building menu
        try:
            self.populate_items()
        except Exception:
            pass

    def add_item(self, category: str, item_name: str, qty_entry: tk.Entry) -> None:
        if self.controller.current_user_id is None:
            messagebox.showerror("Not logged in", "Please log in to add items")
            return
        raw = qty_entry.get().strip()
        try:
            qty = int(raw)
            if qty < 1:
                raise ValueError
        except Exception:
            messagebox.showerror("Invalid quantity", "Enter a positive integer quantity")
            return

        unit_price = self.controller.menu_data.get(category, {}).get(item_name)
        if unit_price is None:
            messagebox.showerror("Item error", "Price information not found")
            return

        item_total = unit_price * qty
        orders_mod.add_order_item(self.controller.current_user_id, category, item_name, qty, item_total)
        messagebox.showinfo("Added", f"Added {qty} x {item_name} to your order")

    def populate_items(self) -> None:
        items = []
        for cat, item_map in self.controller.menu_data.items():
            for item in item_map.keys():
                items.append(f"{cat} | {item}")
        self.item_combo["values"] = items

    def add_selected_item(self) -> None:
        if self.controller.current_user_id is None:
            messagebox.showerror("Not logged in", "Please log in to add items")
            return

        raw = self.sel_qty_entry.get().strip()
        try:
            qty = int(raw)
            if qty < 1:
                raise ValueError
        except Exception:
            messagebox.showerror("Invalid quantity", "Enter a positive integer quantity")
            return

        try:
            category, item_name = self.item_var.get().split(" | ", 1)
        except Exception:
            messagebox.showerror("Selection error", "Please select a menu item")
            return

        unit_price = self.controller.menu_data.get(category, {}).get(item_name)
        if unit_price is None:
            messagebox.showerror("Item error", "Price information not found")
            return

        item_total = unit_price * qty
        orders_mod.add_order_item(self.controller.current_user_id, category, item_name, qty, item_total)
        messagebox.showinfo("Added", f"Added {qty} x {item_name} to your order")

    def logout(self) -> None:
        self.controller.current_user_id = None
        self.controller.show_frame("LoginFrame")


class OrdersFrame(tk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller

        top = tk.Frame(self)
        top.pack(fill=tk.X, pady=6)
        tk.Label(top, text="My Orders", font=(None, 18)).pack(side=tk.LEFT, padx=10)
        tk.Button(top, text="Back to Menu", command=lambda: controller.show_frame("MenuFrame")).pack(side=tk.RIGHT, padx=6)

        self.list_frame = tk.Frame(self)
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        bottom = tk.Frame(self)
        bottom.pack(fill=tk.X, pady=6)
        tk.Button(bottom, text="Confirm Orders", command=self.confirm_orders).pack(side=tk.RIGHT, padx=6)

    def on_show(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()

        user_id = self.controller.current_user_id
        if user_id is None:
            messagebox.showerror("Not logged in", "Please log in to view orders")
            self.controller.show_frame("LoginFrame")
            return

        orders = orders_mod.get_pending_orders(user_id)
        if not orders:
            tk.Label(self.list_frame, text="No pending orders.").pack()
            return

        for o in orders:
            frame = tk.Frame(self.list_frame, bd=1, relief=tk.SOLID, padx=6, pady=6)
            frame.pack(fill=tk.X, pady=4)
            tk.Label(frame, text=o.get("menu_item", "")).grid(row=0, column=0, sticky="w")
            qty_var = tk.StringVar(value=str(o.get("quantity", 0)))
            qty_entry = tk.Entry(frame, textvariable=qty_var, width=5)
            qty_entry.grid(row=0, column=1)
            total_label = tk.Label(frame, text=f"RM{o.get('item_total', 0):.2f}")
            total_label.grid(row=0, column=2, padx=8)

            def do_update(order_id=o["order_item_id"], entry=qty_entry, item_name=o["menu_item"], category=o.get("menu_cat")):
                try:
                    new_q = int(entry.get())
                    if new_q < 1:
                        raise ValueError
                except Exception:
                    messagebox.showerror("Invalid quantity", "Enter a positive integer")
                    return
                price = self.controller.menu_data.get(category, {}).get(item_name, 0)
                new_total = price * new_q
                orders_mod.update_order_item(order_id, new_q, new_total)
                self.refresh()

            def do_delete(order_id=o["order_item_id"]):
                orders_mod.delete_order_item(order_id)
                self.refresh()

            tk.Button(frame, text="Update", command=do_update).grid(row=0, column=3, padx=4)
            tk.Button(frame, text="Delete", command=do_delete).grid(row=0, column=4, padx=4)

    def confirm_orders(self) -> None:
        user_id = self.controller.current_user_id
        if user_id is None:
            messagebox.showerror("Not logged in", "Please log in to confirm orders")
            return

        # gather pending orders first
        pending = orders_mod.get_pending_orders(user_id)
        if not pending:
            messagebox.showinfo("No orders", "You have no pending orders to confirm")
            return

        # Mark as confirmed
        orders_mod.confirm_orders(user_id)

        # Update sales file
        sales_data = sales_mod.load_sales()
        for o in pending:
            item_name = o.get("menu_item")
            qty = int(o.get("quantity", 0))
            total = float(o.get("item_total", 0.0))
            sales_mod.update_sales(sales_data, item_name, qty, total)
        sales_mod.save_sales(sales_data)

        messagebox.showinfo("Confirmed", "Your orders have been confirmed")
        self.controller.show_frame("MenuFrame")


class OwnerSalesFrame(tk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Sales Summary", font=(None, 18)).pack(pady=8)
        self.list_frame = tk.Frame(self)
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        tk.Button(self, text="Back", command=lambda: controller.show_frame("LoginFrame")).pack(pady=6)

    def on_show(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()
        sales_data = sales_mod.load_sales()
        summary = sales_mod.get_sales_summary(sales_data)
        if not summary:
            tk.Label(self.list_frame, text="No sales recorded.").pack()
            return
        for s in summary:
            tk.Label(self.list_frame, text=f"{s['item_name']} — qty: {s['quantity']} — RM{s['revenue']:.2f}").pack(anchor="w")


def run_app(menu_data: Optional[Dict[str, Dict[str, float]]] = None) -> None:
    app = App(menu_data=menu_data)
    app.mainloop()


if __name__ == "__main__":
    run_app()
