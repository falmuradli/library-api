import os

from flask import Flask, jsonify

from db import DB_PATH, init_db
from errors import LibraryError
from routers.books import books_bp
from routers.loans import loans_bp
from routers.members import members_bp
from routers.reports import reports_bp

app = Flask(__name__)
app.register_blueprint(books_bp)
app.register_blueprint(members_bp)
app.register_blueprint(loans_bp)
app.register_blueprint(reports_bp)


@app.errorhandler(LibraryError)
def handle_library_error(error):
    return jsonify({"error": error.message}), error.status


if not os.path.exists(DB_PATH):
    init_db()


if __name__ == "__main__":
    app.run(debug=False)
