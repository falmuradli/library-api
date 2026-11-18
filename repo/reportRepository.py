def open_loans_with_names(conn):
    return conn.execute(
        """
        SELECT loans.id, books.title, members.name AS member, loans.due_date
        FROM loans
        JOIN books ON books.id = loans.book_id
        JOIN members ON members.id = loans.member_id
        WHERE loans.returned = 0
        """
    ).fetchall()


def count_books(conn):
    return conn.execute("SELECT COUNT(*) AS total FROM books").fetchone()["total"]
