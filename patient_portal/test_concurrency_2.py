# Patient is trying to create new appointment
# and provider is rescheduling the existing appointment
# with the same time_slot
# "Concurrent create vs reschedule testing"

import os
import django
import threading

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from appointments.models import Patient, Provider
from appointments.services import (
    create_appointment,
    reschedule_appointment,
)


provider = Provider.objects.first()
patient = Patient.objects.first()


existing_appointment = create_appointment(
    patient=patient,
    provider=provider,
    appointment_type="CONSULTATION",
    scheduled_at="2026-08-26T10:00:00",
)

print(
    f"Existing appointment created: {existing_appointment.id}"
)


def create_new_appointment():
    try:
        appointment = create_appointment(
            patient=patient,
            provider=provider,
            appointment_type="CONSULTATION",
            scheduled_at="2026-08-26T11:00:00",
        )

        print(
            f"CREATE SUCCESS: Appointment {appointment.id}"
        )

    except Exception as e:
        print(
            f"CREATE FAILED: {type(e).__name__}: {e}"
        )


def reschedule_existing_appointment():
    try:
        appointment = reschedule_appointment(
            appointment_id=existing_appointment.id,
            expected_version=existing_appointment.version,
            new_scheduled_at="2026-08-26T11:00:00",
        )

        print(
            f"RESCHEDULE SUCCESS: Appointment {appointment.id}"
        )

    except Exception as e:
        print(
            f"RESCHEDULE FAILED: {type(e).__name__}: {e}"
        )


thread1 = threading.Thread(
    target=create_new_appointment
)

thread2 = threading.Thread(
    target=reschedule_existing_appointment
)

thread1.start()
thread2.start()

thread1.join()
thread2.join()



# "Sqlite" Output:

# (app_venv) C:\Users\mihir\Desktop\Qualifacts\patient_portal>python test_concurrency_2.py
# Existing appointment created: 20
# RESCHEDULE FAILED: OperationalError: database is locked
# CREATE SUCCESS: Appointment 21


# "MySQL" Output:

# (app_venv) C:\Users\mihir\Desktop\Qualifacts\patient_portal_mysql>python test_concurrency_2.py
# Existing appointment created: 2
# CREATE SUCCESS: Appointment 3
# RESCHEDULE FAILED: ValueError: Provider already has an overlapping appointment.