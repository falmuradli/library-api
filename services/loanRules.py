from fines import days_late, fine_for

LOAN_DAYS = 14
LOAN_LIMITS = {"student": 3, "staff": 5}
MAX_RENEWALS = 1


def loan_limit(member_type):
    return LOAN_LIMITS.get(member_type, LOAN_LIMITS["student"])


def current_fine(loan, today):
    if loan["returned"]:
        return loan["fine"]
    return fine_for(loan["due_date"], today)


def amount_owed(loan, today):
    if loan["returned"] and loan["fine_paid"]:
        return 0
    return current_fine(loan, today)


def total_owed(loans, today):
    return sum(amount_owed(loan, today) for loan in loans)


def count_open_loans(loans):
    return sum(not loan["returned"] for loan in loans)


def is_overdue(loan, today):
    return not loan["returned"] and days_late(loan["due_date"], today) > 0
