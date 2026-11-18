import os
import re
import sqlite3
from contextlib import closing
from datetime import date, timedelta
import sqlite3
from datetime import date, timedelta
from flask import Blueprint, jsonify, request
loans_bp = Blueprint("loans", __name__)
CURRENT_MEMBER = None

from flask import Flask, jsonify, request

app = Flask(__name__)

CURRENT_MEMBER = None


def init_db():
    conn = sqlite3.connect("library.db")
    conn.executescript(
        """
        DROP TABLE IF EXISTS books;
        DROP TABLE IF EXISTS members;
        DROP TABLE IF EXISTS loans;
        CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, author TEXT, isbn TEXT, available INTEGER DEFAULT 1
        );
        CREATE TABLE members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, email TEXT UNIQUE, type TEXT
        );
        CREATE TABLE loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER, member_id INTEGER, due_date TEXT,
            returned INTEGER DEFAULT 0, fine REAL DEFAULT 0,
            fine_paid INTEGER DEFAULT 0, renewals INTEGER DEFAULT 0,
            checked_out TEXT
        );
        """
    )
    books = [
        ("Clean Code", "Robert C. Martin", "9780132350884", 1),
        ("The Pragmatic Programmer", "Andrew Hunt", "9780135957059", 1),
        ("Design Patterns", "Erich Gamma", "9780201633610", 1),
        ("Refactoring", "Martin Fowler", "9780134757599", 1),
        ("Code Complete", "Steve McConnell", "9780735619678", 0),
    ]
    conn.executemany("INSERT INTO books (title, author, isbn, available) VALUES (?, ?, ?, ?)", books)
    members = [
        ("Sam Rivera", "sam@campus.edu", "student"),
        ("Dr. Noor Aziz", "noor@campus.edu", "staff"),
        ("Alex Chen", "alex@campus.edu", "student"),
    ]
    conn.executemany("INSERT INTO members (name, email, type) VALUES (?, ?, ?)", members)
    today = date.today()
    conn.execute(
        "INSERT INTO loans (book_id, member_id, due_date, checked_out) VALUES (5, 3, ?, ?)",
        ((today - timedelta(days=5)).isoformat(), (today - timedelta(days=19)).isoformat()),
    )
    conn.commit()
    conn.close()


# ---------- helpers ----------


def check(value, kind):
    if kind == "email":
        return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(value)) is not None
    elif kind == "isbn":
        digits = str(value).replace("-", "")
        return digits.isdigit() and len(digits) in (10, 13)
    elif kind == "date":
        try:
            date.fromisoformat(str(value))
            return True
        except ValueError:
            return False
    elif kind == "member_type":
        return value in ("student", "staff")
    return False


def money(x):
    return round(float(x), 2)


def notify(kind, title="", send=True):
    if not send:
        return
    if kind == "checkout":
        subject = "Book checked out"
        body = "You checked out " + title
    elif kind == "renew":
        subject = "Loan renewed"
        body = "You renewed " + title
    else:
        subject = "Library notice"
        body = title
    with open("outbox.txt", "a") as f:
        f.write("TO: " + CURRENT_MEMBER[2] + " | SUBJECT: " + subject + " | BODY: " + body + "\n")


# ---------- books ----------

# ---------- members ----------

# ---------- loans ----------

# ---------- reports ----------


@app.route("/reports/overdue", methods=["GET"])
def report_overdue():
    conn = sqlite3.connect("library.db")
    rows = conn.execute(
        """
        SELECT loans.id, books.title, members.name, loans.due_date
        FROM loans
        JOIN books ON books.id = loans.book_id
        JOIN members ON members.id = loans.member_id
        WHERE loans.returned = 0
        """
    ).fetchall()
    conn.close()
    items = []
    total = 0
    for r in rows:
        days_late = (date.today() - date.fromisoformat(r[3])).days
        if days_late > 0:
            fine = days_late * 0.5
            total += fine
            items.append(
                {"loan_id": r[0], "title": r[1], "member": r[2], "days_late": days_late, "fine": money(fine)}
            )
    return jsonify({"items": items, "total_fines": money(total)})


@app.route("/reports/summary", methods=["GET"])
def report_summary():
    conn = sqlite3.connect("library.db")
    total_books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    rows = conn.execute("SELECT * FROM loans").fetchall()
    conn.close()
    on_loan = 0
    outstanding = 0
    for loan in rows:
        if loan[4] == 0:
            on_loan += 1
            days_late = (date.today() - date.fromisoformat(loan[3])).days
            outstanding += max(0, days_late) * 0.50
        elif loan[6] == 0:
            outstanding += loan[5]
    return jsonify({"total_books": total_books, "on_loan": on_loan, "fines_outstanding": money(outstanding)})


# ---------- resource updates and deletion ----------


def json_object():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


@app.route("/books/<int:book_id>", methods=["PUT", "PATCH"])
def update_book(book_id):
    data = json_object()
    if data is None:
        return jsonify({"error": "a JSON object is required"}), 400
    if set(data) - {"title", "author", "isbn"}:
        return jsonify({"error": "only title, author and isbn can be updated; availability is managed by loans"}), 400
    with closing(sqlite3.connect("library.db")) as conn, conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        if row is None:
            return jsonify({"error": "book not found"}), 404
        if request.method == "PUT" and not {"title", "author", "isbn"} <= data.keys():
            return jsonify({"error": "PUT requires title, author and isbn"}), 400
        updated = dict(row)
        updated.update(data)
        if any(not isinstance(updated[key], str) or not updated[key].strip() for key in ("title", "author")):
            return jsonify({"error": "title and author must be nonempty strings"}), 400
        if not isinstance(updated["isbn"], str) or not check(updated["isbn"], "isbn"):
            return jsonify({"error": "invalid isbn"}), 400
        conn.execute("UPDATE books SET title = ?, author = ?, isbn = ? WHERE id = ?",
                     (updated["title"], updated["author"], updated["isbn"], book_id))
    return get_book(book_id)


@app.route("/members/<int:member_id>", methods=["PUT", "PATCH"])
def update_member(member_id):
    data = json_object()
    if data is None:
        return jsonify({"error": "a JSON object is required"}), 400
    if set(data) - {"name", "email", "type"}:
        return jsonify({"error": "only name, email and type can be updated"}), 400
    conn = sqlite3.connect("library.db")
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
        if row is None:
            return jsonify({"error": "member not found"}), 404
        if request.method == "PUT" and not {"name", "email", "type"} <= data.keys():
            return jsonify({"error": "PUT requires name, email and type"}), 400
        updated = dict(row)
        updated.update(data)
        if not isinstance(updated["name"], str) or not updated["name"].strip():
            return jsonify({"error": "name must be a nonempty string"}), 400
        if not isinstance(updated["email"], str) or not check(updated["email"], "email"):
            return jsonify({"error": "invalid email"}), 400
        if not check(updated["type"], "member_type"):
            return jsonify({"error": "type must be student or staff"}), 400
        limit = 5 if updated["type"] == "staff" else 3
        count = conn.execute("SELECT COUNT(*) FROM loans WHERE member_id = ? AND returned = 0", (member_id,)).fetchone()[0]
        if count > limit:
            return jsonify({"error": "active loans exceed the new member type's limit"}), 409
        conn.execute("UPDATE members SET name = ?, email = ?, type = ? WHERE id = ?",
                     (updated["name"], updated["email"], updated["type"], member_id))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "email already registered"}), 409
    finally:
        conn.close()
    return get_member(member_id)


@app.route("/members/<int:member_id>", methods=["DELETE"])
def delete_member(member_id):
    conn = sqlite3.connect("library.db")
    try:
        conn.execute("BEGIN IMMEDIATE")
        member = conn.execute("SELECT id FROM members WHERE id = ?", (member_id,)).fetchone()
        if member is None:
            return jsonify({"error": "member not found"}), 404
        active = conn.execute("SELECT id FROM loans WHERE member_id = ? AND returned = 0", (member_id,)).fetchone()
        if active is not None:
            return jsonify({"error": "member has active loans"}), 409
        unpaid = conn.execute("SELECT id FROM loans WHERE member_id = ? AND fine > 0 AND fine_paid = 0", (member_id,)).fetchone()
        if unpaid is not None:
            return jsonify({"error": "member has unpaid fines"}), 409
        conn.execute("DELETE FROM members WHERE id = ?", (member_id,))
        conn.commit()
        return "", 204
    finally:
        conn.close()


@app.route("/loans/<int:loan_id>", methods=["PUT", "PATCH"])
def update_loan(loan_id):
    # Resource updates use the same one-time, 14-day extension as /renew.
    # Other loan fields describe checkout, return or payment events.
    data = json_object()
    if data is None or set(data) != {"due_date"}:
        return jsonify({"error": "provide only due_date; use checkout, return and pay-fine endpoints for other changes"}), 400
    if not check(data["due_date"], "date"):
        return jsonify({"error": "invalid due_date"}), 400
    with closing(sqlite3.connect("library.db")) as conn, conn:
        loan = conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
    if loan is None:
        return jsonify({"error": "loan not found"}), 404
    if data["due_date"] == loan[3]:
        return get_loan(loan_id)
    expected = (date.fromisoformat(loan[3]) + timedelta(days=14)).isoformat()
    if data["due_date"] != expected:
        return jsonify({"error": "due_date can only be extended by 14 days"}), 400
    return renew_loan(loan_id)


@app.route("/loans/<int:loan_id>", methods=["DELETE"])
def delete_loan(loan_id):
    conn = sqlite3.connect("library.db")
    try:
        conn.execute("BEGIN IMMEDIATE")
        loan = conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
        if loan is None:
            return jsonify({"error": "loan not found"}), 404
        if not loan[4]:
            return jsonify({"error": "return the book before deleting the loan"}), 409
        if loan[5] > 0 and not loan[6]:
            return jsonify({"error": "pay the fine before deleting the loan"}), 409
        conn.execute("DELETE FROM loans WHERE id = ?", (loan_id,))
        conn.commit()
        return "", 204
    finally:
        conn.close()


@app.before_request
def validate_json_body():
    if request.method in ("POST", "PUT", "PATCH") and request.path in ("/books", "/members", "/loans"):
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "a JSON object is required"}), 400
        text_fields = {"/books": ("title", "author", "isbn"), "/members": ("name", "email", "type"), "/loans": ("due_date",)}
        for field in text_fields[request.path]:
            if field in data and (not isinstance(data[field], str) or not data[field].strip()):
                return jsonify({"error": field + " must be a nonempty string"}), 400
        if request.path == "/loans":
            for field in ("book_id", "member_id"):
                if field in data and (type(data[field]) is not int or data[field] <= 0):
                    return jsonify({"error": field + " must be a positive integer"}), 400
            if "due_date" in data and check(data["due_date"], "date") and date.fromisoformat(data["due_date"]) < date.today():
                return jsonify({"error": "due_date cannot be in the past"}), 400


if not os.path.exists("library.db"):
    init_db()


if __name__ == "__main__":
    app.run(debug=False)


