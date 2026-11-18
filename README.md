# Campus Library API: Refactoring Activity

This API works and its tests pass, but all the code is in one file. Your job is to reorganize it to **reduce coupling and increase cohesion, without changing what the API does**.

## Set up

Fork this repository, clone your fork and install the requirements. The [before-class setup](before-class-setup.md) has every step, including what to install first and the Windows commands.

```bash
git clone https://github.com/YOUR-USERNAME/library-api.git
cd library-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Check that everything works:

```bash
python -m unittest               # run the tests: 53 should pass
python -m flask run --port 8000  # start the API (Ctrl+C to stop)
```

With the API running, open these in your browser:

- <http://localhost:8000/books>
- <http://localhost:8000/reports/overdue>

To reset the data, stop the API and delete `library.db`. It is recreated the next time the API starts.

## Your task

### 1. Diagnose (10 minutes)

Read `app.py` **without changing it**. List at least five design problems. For each one, note:

- where it is
- whether it is mainly a coupling or a cohesion problem
- what future change it would make harder

### 2. Refactor (30 minutes)

Reorganize the code in small steps, and run the tests after each step. You decide the structure.

Fill in the "Before" column of the table below before you start.

### 3. Change request (10 minutes)

Your instructor will give you a new requirement. Implement it in your refactored code and count the places you had to edit.

## Rules

1. **Do not change `test_api.py`.**
2. **Keep `app.py` in this folder**, and make sure it still provides `app` and `init_db`. It can be very short.
3. **Keep `library.db` and `outbox.txt` as relative paths**, so they are created in the folder the API runs from. `outbox.txt` stands in for a real mail server.
4. **Keep the API's behavior the same:** the same URLs, status codes and JSON.

## Measure your work

| Measure | Before | After |
|---|---|---|
| Tests passing | 7 of 53 | 53 of 53 |
| Lines in the largest application file | 316 | 146 |
| Places where the fine rate appears | 7 | 1 |
| Route handlers containing SQL | 21 | 0 |
| Places edited for the change request | n/a | Pending instructor requirement |
| Can the fine rule be tested without HTTP or a database? | No | Yes |

The baseline is the partially refactored project as checked in before this work. The SQL count includes the unregistered handlers in the three router files.

### Diagnosis

| Where | Main issue | Change made harder |
|---|---|---|
| Route registration | Coupling | The extracted routers depended on an undefined `app`, so moving handlers disabled their endpoints. |
| Book, member, loan and report handlers | Cohesion | HTTP handling, SQL and business rules shared functions, so changing storage meant editing HTTP handlers. |
| Loan, member and report calculations | Cohesion | The daily fine rate appeared in seven calculations, so a rate change could leave reports and checkout eligibility disagreeing. |
| Loan notifications | Coupling | The sender read a mutable global member, so concurrent requests could use the wrong recipient. |
| Resource updates in `app.py` | Coupling | Update handlers called other route functions, so a change to a read or renew handler could change update behavior. |

## Questions to answer

1. Which module is the most cohesive? Describe its one job in a sentence.
2. Which dependency did you remove, and what can now change independently because of that?
3. What coupling remains, and why did you accept it?

1. `fines.py` handles late-day and fine calculations.
2. Routers no longer depend on SQL or SQLite connections, so database queries can change independently of Flask request handling.
3. Services share named row fields with repositories and pass one connection across related writes. This lets checkout and return update the loan and book availability in a single transaction.

## API reference

| Method | URL | Purpose |
|---|---|---|
| GET | `/books` | List books (`?available=true` to filter) |
| POST | `/books` | Add a book |
| GET | `/books/<id>` | Get a book |
| DELETE | `/books/<id>` | Delete a book that isn't on loan |
| GET | `/members` | List members |
| POST | `/members` | Add a member |
| GET | `/members/<id>` | Get a member |
| GET | `/members/<id>/loans` | Get a member's loans and amount owed |
| GET | `/loans` | List loans (`?overdue=true` to filter) |
| POST | `/loans` | Check out a book |
| GET | `/loans/<id>` | Get a loan |
| POST | `/loans/<id>/return` | Return a book |
| POST | `/loans/<id>/renew` | Renew a loan |
| POST | `/loans/<id>/pay-fine` | Pay a fine |
| GET | `/reports/overdue` | List overdue loans |
| GET | `/reports/summary` | Get library totals |

## Library rules

- Loans last 14 days and can be renewed once, for 14 more days, if they aren't overdue.
- Late returns cost $0.50 per day.
- Students can have 3 open loans, and staff can have 5.
- Members who owe money can't check out books.
