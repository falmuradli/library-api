from datetime import date

FINE_PER_DAY = 0.50


def days_late(due_date, today=None):
    return ((today or date.today()) - date.fromisoformat(due_date)).days


def fine_for(due_date, today=None):
    return max(0, days_late(due_date, today)) * FINE_PER_DAY


def money(amount):
    return round(float(amount), 2)
