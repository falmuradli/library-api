from datetime import date, timedelta

from db import connect
from errors import bad_request, conflict, not_found
from fines import fine_for, money
from notifications import send_email
from repo import bookRepository as books
from repo import loansRepository as loans
from services import loanRules as rules
from services.booksService import require_book
from services.membersService import require_member
from validation import is_valid_date, require_object, validate_text_fields


def require_loan(conn, loan_id):
    loan = loans.get_loan(conn, loan_id)
    if loan is None:
        raise not_found("loan not found")
    return loan


def with_current_fine(loan, today):
    return {**dict(loan), "current_fine": money(rules.current_fine(loan, today))}


def list_loans(only_overdue):
    today = date.today()
    with connect() as conn:
        rows = loans.list_loans(conn)
    return [
        with_current_fine(loan, today)
        for loan in rows
        if not only_overdue or rules.is_overdue(loan, today)
    ]


def get_loan(loan_id):
    with connect() as conn:
        return with_current_fine(require_loan(conn, loan_id), date.today())


def create_loan(data):
    require_object(data)
    validate_text_fields(data, ("due_date",))
    for field in ("book_id", "member_id"):
        if field in data and (type(data[field]) is not int or data[field] <= 0):
            raise bad_request(f"{field} must be a positive integer")
    if "book_id" not in data or "member_id" not in data:
        raise bad_request("book_id and member_id are required")
    if "due_date" in data and not is_valid_date(data["due_date"]):
        raise bad_request("invalid due_date")

    today = date.today()
    due_date = data.get("due_date") or (today + timedelta(days=rules.LOAN_DAYS)).isoformat()
    with connect(write=True) as conn:
        book = require_book(conn, data["book_id"])
        member = require_member(conn, data["member_id"])
        if book["available"] == 0:
            raise conflict("book is not available")
        account_loans = loans.member_loans(conn, member["id"])
        if rules.total_owed(account_loans, today) > 0:
            raise conflict("member has unpaid fines")
        if rules.count_open_loans(account_loans) >= rules.loan_limit(member["type"]):
            raise conflict("loan limit reached")
        loan = loans.create_loan(conn, book["id"], member["id"], due_date, today.isoformat())
        books.set_availability(conn, book["id"], False)

    send_email(member["email"], "Book checked out", f"You checked out {book['title']}")
    return loan


def return_book(loan_id):
    with connect(write=True) as conn:
        loan = require_loan(conn, loan_id)
        if loan["returned"]:
            raise conflict("loan already returned")
        fine = fine_for(loan["due_date"])
        member = require_member(conn, loan["member_id"])
        book = require_book(conn, loan["book_id"])
        updated = loans.return_loan(conn, loan_id, fine)
        books.set_availability(conn, book["id"], True)

    send_email(member["email"], "Book returned", f"You returned {book['title']}. Fine: ${money(fine)}")
    return updated


def renew_loan(loan_id, requested_due_date=None):
    today = date.today()
    with connect(write=True) as conn:
        loan = require_loan(conn, loan_id)
        if requested_due_date == loan["due_date"]:
            return with_current_fine(loan, today)
        if requested_due_date is not None and requested_due_date != extended_due_date(loan["due_date"]):
            raise bad_request(f"due_date can only be extended by {rules.LOAN_DAYS} days")
        if loan["returned"]:
            raise conflict("loan already returned")
        if rules.is_overdue(loan, today):
            raise conflict("overdue loans cannot be renewed")
        if loan["renewals"] >= rules.MAX_RENEWALS:
            raise conflict("loan was already renewed")
        member = require_member(conn, loan["member_id"])
        book = require_book(conn, loan["book_id"])
        new_due = requested_due_date or extended_due_date(loan["due_date"])
        updated = loans.renew_loan(conn, loan_id, new_due)

    send_email(member["email"], "Loan renewed", f"You renewed {book['title']}")
    return updated


def extended_due_date(due_date):
    try:
        return (date.fromisoformat(due_date) + timedelta(days=rules.LOAN_DAYS)).isoformat()
    except OverflowError as error:
        raise bad_request("renewed due_date is outside the supported date range") from error


def update_loan(loan_id, data):
    if not isinstance(data, dict) or data.keys() != {"due_date"}:
        raise bad_request("provide only due_date; use checkout, return and pay-fine endpoints for other changes")
    if not is_valid_date(data["due_date"]):
        raise bad_request("invalid due_date")
    return renew_loan(loan_id, data["due_date"])


def pay_fine(loan_id):
    with connect(write=True) as conn:
        loan = require_loan(conn, loan_id)
        if not loan["returned"]:
            raise conflict("return the book before paying")
        if loan["fine"] <= 0 or loan["fine_paid"]:
            raise conflict("no fine to pay")
        member = require_member(conn, loan["member_id"])
        updated = loans.mark_fine_paid(conn, loan_id)

    send_email(member["email"], "Fine paid", f"We received ${money(loan['fine'])}")
    return updated


def delete_loan(loan_id):
    with connect(write=True) as conn:
        loan = require_loan(conn, loan_id)
        if not loan["returned"]:
            raise conflict("return the book before deleting the loan")
        if loan["fine"] > 0 and not loan["fine_paid"]:
            raise conflict("pay the fine before deleting the loan")
        loans.delete_loan(conn, loan_id)
