from flask import Blueprint, jsonify, request

from routers.serializers import member_loan_json
from services import membersService as members

members_bp = Blueprint("members", __name__)


def member_json(member):
    return {key: member[key] for key in ("id", "name", "email", "type")}


@members_bp.get("/members")
def list_members():
    return jsonify([member_json(member) for member in members.list_members()])


@members_bp.get("/members/<int:member_id>")
def get_member(member_id):
    return jsonify(member_json(members.get_member(member_id)))


@members_bp.post("/members")
def create_member():
    return jsonify(member_json(members.create_member(request.get_json(silent=True)))), 201


@members_bp.route("/members/<int:member_id>", methods=["PUT", "PATCH"])
def update_member(member_id):
    updated = members.update_member(member_id, request.get_json(silent=True), request.method == "PUT")
    return jsonify(member_json(updated))


@members_bp.delete("/members/<int:member_id>")
def delete_member(member_id):
    members.delete_member(member_id)
    return "", 204


@members_bp.get("/members/<int:member_id>/loans")
def member_loans(member_id):
    account = members.member_account(member_id)
    account["loans"] = [member_loan_json(loan) for loan in account["loans"]]
    return jsonify(account)
