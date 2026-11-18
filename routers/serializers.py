from fines import money


def member_loan_json(loan):
    return {
        "id": loan["id"],
        "book_id": loan["book_id"],
        "due_date": loan["due_date"],
        "returned": bool(loan["returned"]),
        "fine": money(loan["fine"]),
        "fine_paid": bool(loan["fine_paid"]),
    }


def loan_json(loan):
    result = {
        **member_loan_json(loan),
        "member_id": loan["member_id"],
        "renewals": loan["renewals"],
        "checked_out": loan["checked_out"],
    }
    if "current_fine" in loan.keys():
        result["current_fine"] = loan["current_fine"]
    return result
