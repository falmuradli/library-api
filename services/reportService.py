from datetime import date

from db import connect
from fines import days_late, fine_for, money
from repo import loansRepository as loans
from repo import reportRepository as reports
from services.loanRules import count_open_loans, total_owed


def overdue_report():
    today = date.today()
    with connect() as conn:
        rows = reports.open_loans_with_names(conn)

    items = []
    total = 0
    for row in rows:
        late = days_late(row["due_date"], today)
        if late > 0:
            fine = fine_for(row["due_date"], today)
            total += fine
            items.append({
                "loan_id": row["id"],
                "title": row["title"],
                "member": row["member"],
                "days_late": late,
                "fine": money(fine),
            })
    return {"items": items, "total_fines": money(total)}


def summary_report():
    with connect(snapshot=True) as conn:
        total_books = reports.count_books(conn)
        rows = loans.list_loans(conn)
    return {
        "total_books": total_books,
        "on_loan": count_open_loans(rows),
        "fines_outstanding": money(total_owed(rows, date.today())),
    }
