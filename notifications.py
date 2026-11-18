OUTBOX_PATH = "outbox.txt"


def send_email(email, subject, body):
    with open(OUTBOX_PATH, "a", encoding="utf-8") as outbox:
        outbox.write(f"TO: {email} | SUBJECT: {subject} | BODY: {body}\n")
