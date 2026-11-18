from db import MAX_SQLITE_ID


def list_books(conn, only_available):
    if only_available:
        return conn.execute("SELECT * FROM books WHERE available = 1").fetchall()
    return conn.execute("SELECT * FROM books").fetchall()


def get_book(conn, book_id):
    if book_id > MAX_SQLITE_ID:
        return None
    return conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()


def create_book(conn, title, author, isbn):
    cursor = conn.execute(
        "INSERT INTO books (title, author, isbn, available) VALUES (?, ?, ?, 1)",
        (title, author, isbn),
    )
    return get_book(conn, cursor.lastrowid)


def update_book(conn, book_id, title, author, isbn):
    conn.execute(
        "UPDATE books SET title = ?, author = ?, isbn = ? WHERE id = ?",
        (title, author, isbn, book_id),
    )
    return get_book(conn, book_id)


def set_availability(conn, book_id, available):
    conn.execute("UPDATE books SET available = ? WHERE id = ?", (available, book_id))


def delete_book(conn, book_id):
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
