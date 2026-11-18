from db import MAX_SQLITE_ID


def list_loans(conn):
    return conn.execute("SELECT * FROM loans").fetchall()


def get_loan(conn, loan_id):
    if loan_id > MAX_SQLITE_ID:
        return None
    return conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()


def member_loans(conn, member_id):
    return conn.execute("SELECT * FROM loans WHERE member_id = ?", (member_id,)).fetchall()


def create_loan(conn, book_id, member_id, due_date, checked_out):
    cursor = conn.execute(
        "INSERT INTO loans (book_id, member_id, due_date, checked_out) VALUES (?, ?, ?, ?)",
        (book_id, member_id, due_date, checked_out),
    )
    return get_loan(conn, cursor.lastrowid)


def return_loan(conn, loan_id, fine):
    conn.execute("UPDATE loans SET returned = 1, fine = ? WHERE id = ?", (fine, loan_id))
    return get_loan(conn, loan_id)


def renew_loan(conn, loan_id, due_date):
    conn.execute(
        "UPDATE loans SET due_date = ?, renewals = renewals + 1 WHERE id = ?",
        (due_date, loan_id),
    )
    return get_loan(conn, loan_id)


def mark_fine_paid(conn, loan_id):
    conn.execute("UPDATE loans SET fine_paid = 1 WHERE id = ?", (loan_id,))
    return get_loan(conn, loan_id)


def delete_loan(conn, loan_id):
    conn.execute("DELETE FROM loans WHERE id = ?", (loan_id,))
