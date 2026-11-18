from db import connect
from errors import bad_request, conflict, not_found
from repo import bookRepository as books
from validation import is_nonempty_string, is_valid_isbn, require_object, validate_text_fields

BOOK_FIELDS = {"title", "author", "isbn"}


def require_book(conn, book_id):
    book = books.get_book(conn, book_id)
    if book is None:
        raise not_found("book not found")
    return book


def list_books(only_available):
    with connect() as conn:
        return books.list_books(conn, only_available)


def get_book(book_id):
    with connect() as conn:
        return require_book(conn, book_id)


def create_book(data):
    require_object(data)
    validate_text_fields(data, ("title", "author", "isbn"))
    if not data.get("title") or not data.get("author"):
        raise bad_request("title and author are required")
    if not is_valid_isbn(data.get("isbn")):
        raise bad_request("invalid isbn")
    with connect(write=True) as conn:
        return books.create_book(conn, data["title"], data["author"], data["isbn"])


def update_book(book_id, data, replace):
    require_object(data)
    if data.keys() - BOOK_FIELDS:
        raise bad_request("only title, author and isbn can be updated; availability is managed by loans")
    with connect(write=True) as conn:
        updated = dict(require_book(conn, book_id))
        if replace and not BOOK_FIELDS <= data.keys():
            raise bad_request("PUT requires title, author and isbn")
        updated.update(data)
        if not all(is_nonempty_string(updated[key]) for key in ("title", "author")):
            raise bad_request("title and author must be nonempty strings")
        if not is_valid_isbn(updated["isbn"]):
            raise bad_request("invalid isbn")
        return books.update_book(conn, book_id, updated["title"], updated["author"], updated["isbn"])


def delete_book(book_id):
    with connect(write=True) as conn:
        book = require_book(conn, book_id)
        if book["available"] == 0:
            raise conflict("book is on loan")
        books.delete_book(conn, book_id)
