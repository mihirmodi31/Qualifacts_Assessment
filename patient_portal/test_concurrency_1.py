# Two patient creates request for the same time appointment at same time.
# "Concurrent create vs create testing"

import os
import django
import threading

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from appointments.models import Patient, Provider
from appointments.services import create_appointment


provider = Provider.objects.first()
patient1 = Patient.objects.first()
patient2 = Patient.objects.last()


def create_for_patient(patient):
    try:
        appointment = create_appointment(
            patient=patient,
            provider=provider,
            appointment_type="CONSULTATION",
            scheduled_at="2026-08-25T10:30:00",
        )

        print(
            f"SUCCESS: Appointment {appointment.id} "
            f"created for {patient.name}"
        )

    except Exception as e:
        print(
            f"FAILED for {patient.name}: {type(e).__name__}: {e}"
        )


thread1 = threading.Thread(
    target=create_for_patient,
    args=(patient1,),
)

thread2 = threading.Thread(
    target=create_for_patient,
    args=(patient2,),
)

thread1.start()
thread2.start()

thread1.join()
thread2.join()



# "Sqlite" Output:

# (app_venv) C:\Users\mihir\Desktop\Qualifacts\patient_portal>python test_concurrency_1.py
# FAILED for Mihir Modi: OperationalError: database is locked
# SUCCESS: Appointment 17 created for Mihir Modi


# "MySQL" Output:

# (app_venv) C:\Users\mihir\Desktop\Qualifacts\patient_portal_mysql>python test_concurrency_1.py
# SUCCESS: Appointment 1 created for Mihir
# FAILED for Mihir: ValueError: Provider already has an overlapping appointment.