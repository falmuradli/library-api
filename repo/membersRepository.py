from sqlite3 import IntegrityError

from db import MAX_SQLITE_ID


class DuplicateEmail(Exception):
    pass


def list_members(conn):
    return conn.execute("SELECT * FROM members").fetchall()


def get_member(conn, member_id):
    if member_id > MAX_SQLITE_ID:
        return None
    return conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()


def create_member(conn, name, email, member_type):
    try:
        cursor = conn.execute(
            "INSERT INTO members (name, email, type) VALUES (?, ?, ?)",
            (name, email, member_type),
        )
    except IntegrityError as error:
        raise DuplicateEmail from error
    return get_member(conn, cursor.lastrowid)


def update_member(conn, member_id, name, email, member_type):
    try:
        conn.execute(
            "UPDATE members SET name = ?, email = ?, type = ? WHERE id = ?",
            (name, email, member_type, member_id),
        )
    except IntegrityError as error:
        raise DuplicateEmail from error
    return get_member(conn, member_id)


def delete_member(conn, member_id):
    conn.execute("DELETE FROM members WHERE id = ?", (member_id,))
