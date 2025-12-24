
import sqlite3
from typing import Optional, Tuple

# Registration secret for owner accounts
OWNER_REGISTRATION_CODE = "Crunchy"


def get_connection(db_path: str = "gourmet.db") -> sqlite3.Connection:
	"""Open and return a sqlite3 connection to `db_path`.

	This function only opens the connection; it does not create tables or run
	any queries.
	"""
	return sqlite3.connect(db_path)


def username_exists(username: str, conn: Optional[sqlite3.Connection] = None) -> bool:
	"""Return True if `username` exists in the `customer` table, else False.

	If `conn` is provided it will be used and not closed by this function.
	If `conn` is omitted the function opens and closes its own connection.
	Any database error results in False (caller can decide how to handle it).
	"""
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
	"""Insert a new customer into the `customer` table.

	Rules enforced:
	- All fields must be provided (non-empty)
	- `username` must be unique

	Return contract (always a tuple):
	- (True, "") on success
	- (False, "short human-readable message") on failure

	This function performs no input/output and does not prompt or print.
	It also does not raise on expected failures; callers should inspect the
	returned tuple and display any messages via the GUI layer.
	"""
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
	"""Verify credentials and return `(user_id, role)` if successful, else None.

	Does not print or prompt. Caller must handle the returned value.
	"""
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

