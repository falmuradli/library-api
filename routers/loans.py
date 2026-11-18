from flask import Blueprint, jsonify, request

from routers.serializers import loan_json
from services import loansService as loans

loans_bp = Blueprint("loans", __name__)


@loans_bp.get("/loans")
def list_loans():
    rows = loans.list_loans(request.args.get("overdue") == "true")
    return jsonify([loan_json(loan) for loan in rows])


@loans_bp.get("/loans/<int:loan_id>")
def get_loan(loan_id):
    return jsonify(loan_json(loans.get_loan(loan_id)))


@loans_bp.post("/loans")
def create_loan():
    return jsonify(loan_json(loans.create_loan(request.get_json(silent=True)))), 201


@loans_bp.post("/loans/<int:loan_id>/return")
def return_book(loan_id):
    return jsonify(loan_json(loans.return_book(loan_id)))


@loans_bp.post("/loans/<int:loan_id>/renew")
def renew_loan(loan_id):
    return jsonify(loan_json(loans.renew_loan(loan_id)))


@loans_bp.post("/loans/<int:loan_id>/pay-fine")
def pay_fine(loan_id):
    return jsonify(loan_json(loans.pay_fine(loan_id)))


@loans_bp.route("/loans/<int:loan_id>", methods=["PUT", "PATCH"])
def update_loan(loan_id):
    return jsonify(loan_json(loans.update_loan(loan_id, request.get_json(silent=True))))


@loans_bp.delete("/loans/<int:loan_id>")
def delete_loan(loan_id):
    loans.delete_loan(loan_id)
    return "", 204
