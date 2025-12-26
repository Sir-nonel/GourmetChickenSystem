def load_menu(path="menu.txt"):
	"""Load the menu file and return a nested mapping of categories to items."""
	menu = {}
	cat = None
	with open(path, encoding="utf-8") as f:
		for raw in f:
			line = raw.strip()
			if not line:
				continue
			if line.startswith("#"):
				cat = line.lstrip("#").strip()
				menu.setdefault(cat, {})
				continue
			if "RM" in line and cat is not None:
				name_part, price_part = line.rsplit("RM", 1)
				name = name_part.strip()
				try:
					price = float(price_part.strip())
				except ValueError:
					continue
				menu[cat][name] = price
	return menu


def get_price(menu, category, item_name):
	"""Return the numeric price for a menu item from the loaded menu data."""
	if menu is None:
		raise ValueError("menu is missing")
	return menu.get(category, {}).get(item_name)


if __name__ == "__main__":
	import json
	menu_data = load_menu()
	print(json.dumps(menu_data, indent=2))
	print("Example price lookup:", get_price(menu_data, "Burger", "Chicken Burger"))

