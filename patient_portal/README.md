# Patient Portal Web App

A minimal Django-based patient portal for managing patient appointments.

## Database and Concurrency Note

As allowed by the assignment, the application uses **SQLite** as its default
database so that it can be run locally with minimal setup.

SQLite is suitable for this take-home assignment and provides persistent
storage, but it uses database-level locking for concurrent writes. Therefore,
SQLite is not ideal for demonstrating true concurrent transaction behavior
under simultaneous write requests.

For the concurrency requirements in Problem 4, the application was also
verified using **MySQL/InnoDB**. MySQL/InnoDB provides row-level locking and
allows concurrent transactions to wait for locked rows, which better
represents how the same implementation would behave with a production
database.

### Concurrency Test Results

The concurrency test scripts were executed against both SQLite and
MySQL/InnoDB.

The outputs of these concurrency tests are included as comments at the end of **'test_concurrency_1.py'** and **'test_concurrency_2.py'**.

## Tech Stack

- Python
- Django
- SQLite
- HTML/CSS
- Django ORM

## Project Structure

## Project Structure

```text
patient_portal/
│
├── appointments/
│   ├── models.py
│   ├── services.py
│   ├── views.py
│   ├── urls.py
│   ├── notifications.py
│   ├── admin.py
│   │
│   ├── templates/
│   │   ├── patient.html
│   │   └── provider.html
│   │
│   └── tests/
│       └── ...
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── test_concurrency_1.py
├── test_concurrency_2.py
│
├── manage.py
├── requirements.txt
├── README.md
└── db.sqlite3
```

### Key Files

- **`models.py`** — Data models for patients, providers, appointments, and appointment history.
- **`services.py`** — Core appointment business logic, transactions, version checking, overlap detection, and concurrency handling.
- **`views.py`** — REST API endpoints and patient/provider portal views.
- **`notifications.py`** — Notification stub triggered after successful appointment confirmation.
- **`urls.py`** — API and frontend URL routing.
- **`patient.html`** — Patient portal interface.
- **`provider.html`** — Provider portal interface.
- **`test_concurrency_1.py`** — Concurrent appointment creation test.
- **`test_concurrency_2.py`** — Concurrent appointment creation vs. rescheduling test.
- **`requirements.txt`** — Python dependencies required to run the project.

## Features

### Patient

- View appointments
- Request an appointment
- Cancel confirmed appointments
- View appointment status

### Provider

- View assigned appointments
- Confirm pending appointments
- Reschedule appointments
- View appointment status

## Concurrency and Consistency

### Problem 1 — Concurrent Updates

Appointments use optimistic concurrency control through a `version` field.

When an appointment is updated, the expected version supplied by the client is checked against the current database version.

Updates are also protected using Django's `select_for_update()` inside database transactions.

If another request has already modified the appointment, the second request receives a conflict instead of silently overwriting the first update.

### Problem 2 — Appointment History

All important appointment changes are recorded in `AppointmentHistory`.

The history records:

- Action
- Who made the change
- Previous status
- New status
- Previous scheduled time
- New scheduled time
- Timestamp

This allows previous appointment states to be reconstructed.

### Problem 3 — Notifications

Appointment confirmation uses a notification stub.

The notification is triggered using Django's `transaction.on_commit()`.

This ensures that notification processing does not cause a successful appointment confirmation transaction to roll back.

For production, this could be moved to a background job/queue such as Celery.

### Problem 4 — Provider Overlap

Appointments have a 30-minute duration.

Before creating or rescheduling an appointment, the system checks for overlapping active appointments for the provider.

The provider row is locked using `select_for_update()` inside a database transaction.

This prevents two concurrent requests from both passing the overlap check and creating conflicting appointments.

Concurrency was tested with SQLite and MySQL/InnoDB.

SQLite produced database locking behavior under concurrent writes, while MySQL/InnoDB allowed the transaction waiting behavior and correctly resulted in one appointment succeeding and the other detecting the overlap.

## Setup

Create a virtual environment:

    python -m venv app_venv

Activate it on Windows:

    app_venv\Scripts\activate

Install dependencies:

    pip install -r requirements.txt

Run migrations:

    python manage.py migrate

Start the development server:

    python manage.py runserver

Patient view:

    http://127.0.0.1:8000/appointments/patient/

Provider view:

    http://127.0.0.1:8000/appointments/provider/

