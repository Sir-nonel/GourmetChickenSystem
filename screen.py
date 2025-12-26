import menu as menu_mod
import auth as auth_mod
import orders as orders_mod
import sales as sales_mod
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from typing import Dict, Optional




class App(tk.Tk):
    """Main application window that manages frames, routing, and global state."""
    def __init__(self, menu_data: Optional[Dict[str, Dict[str, float]]] = None):
        super().__init__()
        self.title("Gourmet Chicken System")
        self.geometry("520x550")

        # Global GUI state
        self.current_user_id: Optional[int] = None
        self.current_user_role: Optional[str] = None
        self.menu_data = menu_data or menu_mod.load_menu()

        container = tk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        self.frames: Dict[str, tk.Frame] = {}
        for F in (LoginFrame, RegisterFrame, MenuFrame, OrdersFrame, OwnerSalesFrame, OwnerKitchenFrame):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginFrame")

    def show_frame(self, name: str) -> None:
        """Switch to a named frame and call its optional `on_show` handler."""
        frame = self.frames[name]
        if hasattr(frame, "on_show"):
            try:
                frame.on_show()
            except Exception:
                pass
        frame.tkraise()


class LoginFrame(tk.Frame):
    """Login screen that authenticates users and routes them by role."""
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

    def do_login(self) -> None:
        """Authenticate the entered credentials and navigate to the appropriate view."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        res = auth_mod.login_user(username, password)
        if res is not None:
            user_id, role = res
            self.controller.current_user_id = user_id
            self.controller.current_user_role = role
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            if role == "owner":
                self.controller.show_frame("OwnerKitchenFrame")
            else:
                self.controller.show_frame("MenuFrame")
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")


class RegisterFrame(tk.Frame):
    """Registration screen for creating new customer or owner accounts."""
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

        # Role selection
        tk.Label(form, text="Role").grid(row=4, column=0, sticky="e")
        self.role_var = tk.StringVar(value="customer")
        role_frame = tk.Frame(form)
        role_frame.grid(row=4, column=1, sticky="w")
        tk.Radiobutton(role_frame, text="Customer", variable=self.role_var, value="customer", command=self.update_role_ui).pack(side=tk.LEFT)
        tk.Radiobutton(role_frame, text="Owner", variable=self.role_var, value="owner", command=self.update_role_ui).pack(side=tk.LEFT)

        # Owner registration code (hidden unless role == owner)
        self.owner_code_var = tk.StringVar(value="")
        self.owner_code_label = tk.Label(form, text="Are you an owner?")
        self.owner_code_entry = tk.Entry(form, textvariable=self.owner_code_var, show="*")
        # placed at row 5 when visible
        self.update_role_ui()

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Register", command=self.do_register).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Back", command=lambda: controller.show_frame("LoginFrame")).grid(row=0, column=1, padx=5)

    def do_register(self) -> None:
        """Collect registration data and create a new user via the auth module."""
        name = self.name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        mobilehp = self.mobile_entry.get().strip()
        role = self.role_var.get()
        owner_code = self.owner_code_var.get()
        ok, msg = auth_mod.register_user(name, username, password, mobilehp, role, owner_code)
        if ok:
            messagebox.showinfo("Registered", "Registration successful. Please log in.")
            self.name_entry.delete(0, tk.END)
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.mobile_entry.delete(0, tk.END)
            self.owner_code_var.set("")
            self.controller.show_frame("LoginFrame")
        else:
            messagebox.showerror("Registration Failed", msg)

    def update_role_ui(self) -> None:
        """Show or hide the owner code input depending on selected role."""
        try:
            role = self.role_var.get()
        except Exception:
            role = "customer"
        if role == "owner":
            # show owner code row at row 5
            self.owner_code_label.grid(row=5, column=0, sticky="e")
            self.owner_code_entry.grid(row=5, column=1)
        else:
            # hide owner code widgets
            self.owner_code_label.grid_remove()
            self.owner_code_entry.grid_remove()


class MenuFrame(tk.Frame):
    """Menu browsing screen that allows selecting items and adding them to cart."""
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
        """Rebuild the menu widget list from the loaded menu data."""
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

    def populate_items(self) -> None:
        """Populate the item selection combobox with all available menu items."""
        items = []
        for cat, item_map in self.controller.menu_data.items():
            for item in item_map.keys():
                items.append(f"{cat} | {item}")
        self.item_combo["values"] = items

    def add_selected_item(self) -> None:
        """Validate selection and add the chosen menu item to the user's cart."""
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
        """Log out the current user and show the login frame."""
        self.controller.current_user_id = None
        self.controller.show_frame("LoginFrame")


class OrdersFrame(tk.Frame):
    """Customer orders screen that shows active orders and the current cart."""
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
        self.confirm_button = tk.Button(bottom, text="Confirm Orders", command=self.confirm_orders)
        self.confirm_button.pack(side=tk.RIGHT, padx=6)

    def on_show(self) -> None:
        """Refresh order and cart views when this frame is shown."""
        self.refresh()

    def refresh(self) -> None:
        """Reload active orders and pending cart items from the backend and render them."""
        # Clear current content
        for child in self.list_frame.winfo_children():
            child.destroy()

        user_id = self.controller.current_user_id
        if user_id is None:
            messagebox.showerror("Not logged in", "Please log in to view orders")
            self.controller.show_frame("LoginFrame")
            return

        # Delegate rendering to helpers
        self.render_active_orders(self.list_frame, user_id)
        self.render_cart(self.list_frame, user_id)

    def render_active_orders(self, parent, user_id: int) -> None:
        """Render the user's active orders (preparing and ready) in the given parent widget."""
        tk.Label(parent, text="Active Orders", font=(None, 14, "bold")).pack(anchor="w", pady=(0, 6))

        active_orders = orders_mod.get_active_orders_for_user(user_id)

        if not active_orders:
            tk.Label(parent, text="No active orders.").pack(anchor="w")
            return

        for ao in active_orders:
            order_id = ao.get("order_id")
            status = ao.get("status")
            created_at = ao.get("created_at")
            oframe = tk.Frame(parent, bd=1, relief=tk.SOLID, padx=6, pady=6)
            oframe.pack(fill=tk.X, pady=4)
            status_text = "Kitchen is preparing your order!" if status == "preparing" else ("Your order is ready!" if status == "ready" else status)
            tk.Label(oframe, text=f"Order #{order_id} — {status_text}").pack(anchor="w")
            if created_at:
                tk.Label(oframe, text=f"Created: {created_at}").pack(anchor="w")
            items = orders_mod.get_order_items(order_id)
            order_total = 0.0
            for it in items:
                tk.Label(oframe, text=f"{it.get('menu_item', '')} — qty: {it.get('quantity', 0)} — RM{it.get('item_total', 0.0):.2f}").pack(anchor="w")
                try:
                    order_total += float(it.get('item_total', 0.0))
                except Exception:
                    pass
            tk.Label(oframe, text=f"Total: RM{order_total:.2f}", font=(None, 10, "bold")).pack(anchor="e")
                # allow customers to delete only orders that are ready
            if status == "ready":
                    def do_delete(o_id=order_id):
                        try:
                            orders_mod.delete_order(o_id)
                        except Exception:
                            messagebox.showerror("Error", "Failed to delete order")
                        self.refresh()

                    tk.Button(oframe, text="Delete Order", command=do_delete).pack(pady=6)

    def render_cart(self, parent, user_id: int) -> None:
        """Render the user's current cart items and attach update/delete handlers."""
        tk.Label(parent, text="Current Cart", font=(None, 14, "bold")).pack(anchor="w", pady=(10, 6))

        pending = orders_mod.get_pending_orders(user_id)
        if not pending:
            tk.Label(parent, text="Your cart is empty.").pack()
            return

        for o in pending:
            frame = tk.Frame(parent, bd=1, relief=tk.SOLID, padx=6, pady=6)
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
        """Create an order from the current cart and mark it preparing."""
        user_id = self.controller.current_user_id
        if user_id is None:
            messagebox.showerror("Not logged in", "Please log in to confirm orders")
            return

        # if cart is empty -> inform
        pending = orders_mod.get_pending_orders(user_id)
        if not pending:
            messagebox.showinfo("No orders", "You have no pending orders to confirm")
            return

        # create order row
        order_id = orders_mod.create_order_for_user(user_id)
        if order_id is None:
            messagebox.showerror("Error", "Failed to create order")
            return

        # assign cart items to created order
        orders_mod.assign_cart_items_to_order(user_id, order_id)

        messagebox.showinfo("Confirmed", "Kitchen is preparing your order!")
        self.refresh()


class OwnerSalesFrame(tk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Sales Summary", font=(None, 18)).pack(pady=8)
        self.list_frame = tk.Frame(self)
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        tk.Button(self, text="Back", command=lambda: controller.show_frame("OwnerKitchenFrame")).pack(pady=6)

    def on_show(self) -> None:
        """Refresh the sales summary when this frame becomes visible."""
        self.refresh()

    def refresh(self) -> None:
        """Reload and display sales summary data from the sales module."""
        for child in self.list_frame.winfo_children():
            child.destroy()
        sales_data = sales_mod.load_sales()
        summary = sales_mod.get_sales_summary(sales_data)
        if not summary:
            tk.Label(self.list_frame, text="No sales recorded.").pack()
            return
        for s in summary:
            tk.Label(self.list_frame, text=f"{s['item_name']} — qty: {s['quantity']} — RM{s['revenue']:.2f}").pack(anchor="w")


class OwnerKitchenFrame(tk.Frame):
    """UI for kitchen staff: shows orders with status 'preparing' and allows marking them ready."""
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Kitchen - Preparing Orders", font=(None, 18)).pack(pady=8)
        self.list_frame = tk.Frame(self)
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="View Sales", command=lambda: controller.show_frame("OwnerSalesFrame")).pack(side=tk.LEFT, padx=6)
        def do_logout():
            self.controller.current_user_id = None
            self.controller.current_user_role = None
            self.controller.show_frame("LoginFrame")
        tk.Button(btn_frame, text="Logout", command=do_logout).pack(side=tk.LEFT, padx=6)

    def on_show(self) -> None:
        """Refresh the preparing orders list when this frame is shown."""
        self.refresh()

    def refresh(self) -> None:
        """Reload the list of preparing orders and render receipts for each."""
        for child in self.list_frame.winfo_children():
            child.destroy()

        preparing = orders_mod.get_preparing_orders()
        if not preparing:
            tk.Label(self.list_frame, text="No orders are currently preparing.").pack()
            return

        for row in preparing:
            order_id = row.get("order_id")
            user_id = row.get("user_id")
            customer_name = row.get("customer_name")
            created_at = row.get("created_at")

            # receipt frame
            rframe = tk.Frame(self.list_frame, bd=1, relief=tk.SOLID, padx=8, pady=8)
            rframe.pack(fill=tk.X, pady=6)
            header = f"Order #{order_id}"
            if customer_name:
                name_part = customer_name if customer_name else ""
                header += f" — {name_part}" if name_part else ""
            if created_at:
                header += f" — {created_at}"
            tk.Label(rframe, text=header, font=(None, 12, "bold")).pack(anchor="w")

            # items
            items = orders_mod.get_order_items(order_id)
            total = 0.0
            for it in items:
                name = it.get("menu_item", "")
                qty = it.get("quantity", 0)
                item_total = float(it.get("item_total", 0.0) or 0.0)
                tk.Label(rframe, text=f"{name} — qty: {qty} — RM{item_total:.2f}").pack(anchor="w")
                try:
                    total += item_total
                except Exception:
                    pass

            tk.Label(rframe, text=f"Total: RM{total:.2f}", font=(None, 10, "bold")).pack(anchor="e")

            def mark_ready(o_id=order_id):
                try:
                    orders_mod.mark_order_ready(o_id)
                except Exception:
                     messagebox.showerror("Error", "Failed to update order status.")
                self.refresh()

            tk.Button(rframe, text="Mark Order Ready", command=mark_ready).pack(pady=6)


def run_app(menu_data: Optional[Dict[str, Dict[str, float]]] = None) -> None:
    app = App(menu_data=menu_data)
    app.mainloop()


if __name__ == "__main__":
    run_app()
