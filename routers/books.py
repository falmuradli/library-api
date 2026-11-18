from flask import Blueprint, jsonify, request

from services import booksService as books

books_bp = Blueprint("books", __name__)


def book_json(book):
    return {
        "id": book["id"],
        "title": book["title"],
        "author": book["author"],
        "isbn": book["isbn"],
        "available": bool(book["available"]),
    }


@books_bp.get("/books")
def list_books():
    rows = books.list_books(request.args.get("available") == "true")
    return jsonify([book_json(book) for book in rows])


@books_bp.get("/books/<int:book_id>")
def get_book(book_id):
    return jsonify(book_json(books.get_book(book_id)))


@books_bp.post("/books")
def create_book():
    return jsonify(book_json(books.create_book(request.get_json(silent=True)))), 201


@books_bp.route("/books/<int:book_id>", methods=["PUT", "PATCH"])
def update_book(book_id):
    updated = books.update_book(book_id, request.get_json(silent=True), request.method == "PUT")
    return jsonify(book_json(updated))


@books_bp.delete("/books/<int:book_id>")
def delete_book(book_id):
    books.delete_book(book_id)
    return "", 204
