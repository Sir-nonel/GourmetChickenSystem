
import sqlite3
from typing import Optional, Tuple

# Registration secret for owner accounts
OWNER_REGISTRATION_CODE = "Crunchy"


def get_connection(db_path: str = "gourmet.db") -> sqlite3.Connection:
	"""Return a sqlite3 connection to the application's database file."""
	return sqlite3.connect(db_path)


def username_exists(username: str, conn: Optional[sqlite3.Connection] = None) -> bool:
	"""Return whether the given username already exists in the customer table."""
	close_conn = False
	if conn is None:
		try:
			conn = get_connection()
		except sqlite3.Error:
			return False
		close_conn = True
	try:
		cur = conn.cursor()
		cur.execute("SELECT 1 FROM customer WHERE username = ? LIMIT 1", (username,))
		return cur.fetchone() is not None
	except sqlite3.Error:
		return False
	finally:
		if close_conn:
			conn.close()


def register_user(name: str, username: str, password: str, mobilehp: str, role: str,
				  owner_code: str = "", conn: Optional[sqlite3.Connection] = None) -> Tuple[bool, str]:
	"""Register a new user in the customer table and return success status."""
	# Validate inputs
	if not all([name, username, password, mobilehp, role]):
		return False, "all fields (name, username, password, mobilehp, role) are required"

	# If registering as owner, check owner registration code
	if role == "owner":
		if owner_code != OWNER_REGISTRATION_CODE:
			return False, "You are not the owner!"

	close_conn = False
	if conn is None:
		try:
			conn = get_connection()
		except sqlite3.Error as e:
			return False, f"database error: {e.args[0]}"
		close_conn = True

	try:
		# Check username uniqueness
		if username_exists(username, conn=conn):
			return False, "username already exists"

		cur = conn.cursor()
		cur.execute(
			"INSERT INTO customer (name, username, password, mobilehp, role) VALUES (?, ?, ?, ?, ?)",
			(name, username, password, mobilehp, role),
		)
		conn.commit()
		return True, ""
	except sqlite3.Error as e:
		# Return the error message so caller / GUI can display appropriate feedback
		return False, f"database error: {e.args[0]}"
	finally:
		if close_conn:
			conn.close()


def login_user(username: str, password: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Tuple[int, str]]:
	"""Authenticate credentials and return the user's id and role on success."""
	close_conn = False
	if conn is None:
		try:
			conn = get_connection()
		except sqlite3.Error:
			return None
		close_conn = True
	try:
		cur = conn.cursor()
		cur.execute(
			"SELECT user_id, role FROM customer WHERE username = ? AND password = ? LIMIT 1",
			(username, password),
		)
		row = cur.fetchone()
		if row:
			return int(row[0]), row[1]
		return None
	except sqlite3.Error:
		return None
	finally:
		if close_conn:
			conn.close()

