from django.db import transaction

from .models import Appointment, AppointmentHistory, Provider

from .notifications import send_appointment_confirmation

from datetime import timedelta
from django.utils.dateparse import parse_datetime
from django.utils import timezone

APPOINTMENT_DURATION_MINUTES = 30

def get_appointment_end(scheduled_at):
    return scheduled_at + timedelta(
        minutes=APPOINTMENT_DURATION_MINUTES
    )

def has_overlapping_appointment(provider, scheduled_at, exclude_appointment_id=None):
    # new_end = scheduled_at + timedelta(minutes=APPOINTMENT_DURATION_MINUTES)
    new_end = get_appointment_end(scheduled_at)

    appointments = Appointment.objects.filter(
        provider=provider,
        status__in=[
            Appointment.Status.PENDING,
            Appointment.Status.CONFIRMED,
        ],
    )

    if exclude_appointment_id is not None:
        appointments = appointments.exclude(id = exclude_appointment_id)

    for appointment in appointments:
        existing_start = appointment.scheduled_at
        existing_end = existing_start + timedelta(minutes=APPOINTMENT_DURATION_MINUTES)

        if existing_start < new_end and existing_end > scheduled_at:
            return True

    return False

@transaction.atomic
def create_appointment(*, patient, provider, appointment_type, scheduled_at):

    # Lock the provider so concurrent appointment requests for the same
    # provider cannot pass the overlap check at the same time.
    provider = Provider.objects.select_for_update().get(id=provider.id)  # Problem 4 Solution

    # Convert incoming API datetime strings to Python datetime objects.
    if isinstance(scheduled_at, str):
        scheduled_at = parse_datetime(scheduled_at)

    if scheduled_at is None:
        raise ValueError("Invalid scheduled_at format.")

    if timezone.is_naive(scheduled_at):
        scheduled_at = timezone.make_aware(scheduled_at)

    if has_overlapping_appointment(provider, scheduled_at):
        raise ValueError("Provider already has an overlapping appointment.")

    appointment = Appointment.objects.create(
        patient=patient,
        provider=provider,
        appointment_type=appointment_type,
        scheduled_at=scheduled_at,
        status=Appointment.Status.PENDING,
        version=1,
    )
    AppointmentHistory.objects.create(
        appointment=appointment,
        action=AppointmentHistory.Action.CREATED,
        changed_by=AppointmentHistory.ChangedBy.PATIENT,
        old_status="",
        new_status=Appointment.Status.PENDING,
        old_scheduled_at=None,
        new_scheduled_at=scheduled_at,
    )
    return appointment

@transaction.atomic
def confirm_appointment(*, appointment_id, expected_version):

    # Lock the appointment so concurrent updates are serialized.
    # The version check below prevents an outdated client from overwriting
    # a change that was already made by another request.
    appointment = Appointment.objects.select_for_update().get(id=appointment_id)        # problem 1 solution

    if appointment.version != expected_version:
        raise ValueError("Appointment has been updated. Please refresh and try again.")

    if appointment.status != Appointment.Status.PENDING:
        raise ValueError("Only pending appointments can be confirmed.")

    old_status = appointment.status

    appointment.status = Appointment.Status.CONFIRMED
    appointment.version += 1
    appointment.save()

    AppointmentHistory.objects.create(
        appointment=appointment,
        action=AppointmentHistory.Action.CONFIRMED,
        changed_by=AppointmentHistory.ChangedBy.PROVIDER,
        old_status=old_status,
        new_status=appointment.status,
        old_scheduled_at=appointment.scheduled_at,
        new_scheduled_at=appointment.scheduled_at,
    )

    # Send the notification only after the database transaction succeeds.
    # A notification failure therefore cannot roll back the confirmation.
    transaction.on_commit(lambda: send_appointment_confirmation(appointment))

    return appointment

@transaction.atomic
def reschedule_appointment(*, appointment_id, expected_version, new_scheduled_at):

    # Lock the appointment to prevent concurrent updates to the same
    # appointment while its version and scheduled time are being changed.
    appointment = Appointment.objects.select_for_update().get(id=appointment_id)  # problem 1 solution

    # Lock the provider so the overlap check and rescheduling operation
    # are protected against concurrent appointment operations.
    provider = Provider.objects.select_for_update().get(id=appointment.provider_id) # problem 4 solution

    # Convert incoming API datetime strings to Python datetime objects.
    if isinstance(new_scheduled_at, str):
        new_scheduled_at = parse_datetime(new_scheduled_at)

    if new_scheduled_at is None:
        raise ValueError("Invalid scheduled_at format.")

    if timezone.is_naive(new_scheduled_at):
        new_scheduled_at = timezone.make_aware(new_scheduled_at)

    if has_overlapping_appointment(appointment.provider, new_scheduled_at, exclude_appointment_id=appointment.id):
        raise ValueError("Provider already has an overlapping appointment.")

    if appointment.version != expected_version:
        raise ValueError("Appointment has been updated. Please refresh and try again.")

    if appointment.status == Appointment.Status.CANCELLED:
        raise ValueError("Cancelled appointments cannot be rescheduled.")

    old_scheduled_at = appointment.scheduled_at

    appointment.scheduled_at = new_scheduled_at
    appointment.version += 1
    appointment.save()

    AppointmentHistory.objects.create(
        appointment=appointment,
        action=AppointmentHistory.Action.RESCHEDULED,
        changed_by=AppointmentHistory.ChangedBy.PROVIDER,
        old_status=appointment.status,
        new_status=appointment.status,
        old_scheduled_at=old_scheduled_at,
        new_scheduled_at=new_scheduled_at,
    )

    return appointment

@transaction.atomic
def cancel_appointment(*, appointment_id, expected_version, changed_by):

    # Lock the appointment so concurrent confirm/cancel/reschedule requests
    # cannot modify the same appointment simultaneously.
    appointment = Appointment.objects.select_for_update().get(id=appointment_id)   # problem 1 solution

    # Lock the provider to keep cancellation consistent with other
    # provider-level appointment operations.
    provider = Provider.objects.select_for_update().get(id=appointment.provider_id)

    if appointment.version != expected_version:
        raise ValueError("Appointment has been updated. Please refresh and try again.")
    
    if appointment.status == Appointment.Status.PENDING:
        raise ValueError("Pending appointments cannot be cancelled.")

    if appointment.status == Appointment.Status.CANCELLED:
        raise ValueError("Appointment is already cancelled.")

    old_status = appointment.status

    appointment.status = Appointment.Status.CANCELLED
    appointment.version += 1
    appointment.save()

    AppointmentHistory.objects.create(
        appointment=appointment,
        action=AppointmentHistory.Action.CANCELLED,
        changed_by=changed_by,
        old_status=old_status,
        new_status=Appointment.Status.CANCELLED,
        old_scheduled_at=appointment.scheduled_at,
        new_scheduled_at=appointment.scheduled_at,
    )

    return appointment