from datetime import date

from db import connect
from errors import bad_request, conflict, not_found
from fines import money
from repo import loansRepository as loans
from repo import membersRepository as members
from services.loanRules import LOAN_LIMITS, count_open_loans, loan_limit, total_owed
from validation import is_nonempty_string, is_valid_email, require_object, validate_text_fields

MEMBER_FIELDS = {"name", "email", "type"}


def require_member(conn, member_id):
    member = members.get_member(conn, member_id)
    if member is None:
        raise not_found("member not found")
    return member


def list_members():
    with connect() as conn:
        return members.list_members(conn)


def get_member(member_id):
    with connect() as conn:
        return require_member(conn, member_id)


def validate_member_details(email, member_type):
    if not is_valid_email(email):
        raise bad_request("invalid email")
    if not isinstance(member_type, str) or member_type not in LOAN_LIMITS:
        raise bad_request("type must be student or staff")


def create_member(data):
    require_object(data)
    validate_text_fields(data, ("name", "email", "type"))
    if not data.get("name"):
        raise bad_request("name is required")
    member_type = data.get("type", "student")
    validate_member_details(data.get("email"), member_type)
    with connect(write=True) as conn:
        try:
            return members.create_member(conn, data["name"], data["email"], member_type)
        except members.DuplicateEmail as error:
            raise conflict("email already registered") from error


def update_member(member_id, data, replace):
    require_object(data)
    if data.keys() - MEMBER_FIELDS:
        raise bad_request("only name, email and type can be updated")
    with connect(write=True) as conn:
        updated = dict(require_member(conn, member_id))
        if replace and not MEMBER_FIELDS <= data.keys():
            raise bad_request("PUT requires name, email and type")
        updated.update(data)
        if not is_nonempty_string(updated["name"]):
            raise bad_request("name must be a nonempty string")
        validate_member_details(updated["email"], updated["type"])
        active = count_open_loans(loans.member_loans(conn, member_id))
        if active > loan_limit(updated["type"]):
            raise conflict("active loans exceed the new member type's limit")
        try:
            return members.update_member(conn, member_id, updated["name"], updated["email"], updated["type"])
        except members.DuplicateEmail as error:
            raise conflict("email already registered") from error


def delete_member(member_id):
    with connect(write=True) as conn:
        require_member(conn, member_id)
        account_loans = loans.member_loans(conn, member_id)
        if count_open_loans(account_loans):
            raise conflict("member has active loans")
        if any(loan["fine"] > 0 and not loan["fine_paid"] for loan in account_loans):
            raise conflict("member has unpaid fines")
        members.delete_member(conn, member_id)


def member_account(member_id):
    with connect(snapshot=True) as conn:
        member = require_member(conn, member_id)
        account_loans = loans.member_loans(conn, member_id)
    return {
        "loans": account_loans,
        "total_owed": money(total_owed(account_loans, date.today())),
        "loans_remaining": loan_limit(member["type"]) - count_open_loans(account_loans),
    }
