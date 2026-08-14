from django.shortcuts import render, redirect

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Patient, Provider, Appointment, AppointmentHistory
from .services import (
    create_appointment,
    confirm_appointment,
    reschedule_appointment,
    cancel_appointment,
)

import json

# API views

@csrf_exempt
def appointment_list(request):
    if request.method == "GET":
        appointments = Appointment.objects.select_related(
            "patient",
            "provider",
        ).all()

        data = []

        for appointment in appointments:
            data.append({
                "id": appointment.id,
                "patient": appointment.patient.name,
                "provider": appointment.provider.name,
                "appointment_type": appointment.appointment_type,
                "scheduled_at": appointment.scheduled_at,
                "status": appointment.status,
                "version": appointment.version,
            })

        return JsonResponse(data, safe=False)
    
    if request.method == "POST":
        data = json.loads(request.body)

        patient = Patient.objects.get(id=data["patient_id"])
        provider = Provider.objects.get(id=data["provider_id"])

        try:
            appointment = create_appointment(
                patient=patient,
                provider=provider,
                appointment_type=data["appointment_type"],
                scheduled_at=data["scheduled_at"],
            )
        except ValueError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=409,
            )
        
        return JsonResponse(
            {
                "id": appointment.id,
                "status": appointment.status,
                "version": appointment.version,
            },
            status=201,
        )
    
    return JsonResponse(
        {"error": "Method not allowed"},
        status=405,
    )
    
    # return JsonResponse({
    #     "message": "Appointment list API"
    # })

@csrf_exempt
def appointment_confirm(request, appointment_id):

    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405,
        )

    data = json.loads(request.body)

    try:
        appointment = confirm_appointment(
            appointment_id=appointment_id,
            expected_version=data["version"],
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=409,
        )

    return JsonResponse({
        "id": appointment.id,
        "status": appointment.status,
        "version": appointment.version,
    })

@csrf_exempt
def appointment_reschedule(request, appointment_id):

    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405,
        )

    data = json.loads(request.body)

    try:
        appointment = reschedule_appointment(
            appointment_id=appointment_id,
            expected_version=data["version"],
            new_scheduled_at=data["scheduled_at"],
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=409,
        )

    return JsonResponse({
        "id": appointment.id,
        "scheduled_at": appointment.scheduled_at,
        "status": appointment.status,
        "version": appointment.version,
    })

@csrf_exempt
def appointment_cancel(request, appointment_id):

    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405,
        )

    data = json.loads(request.body)

    try:
        appointment = cancel_appointment(
            appointment_id=appointment_id,
            expected_version=data["version"],
            changed_by=data["changed_by"],
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=409,
        )

    return JsonResponse({
        "id": appointment.id,
        "status": appointment.status,
        "version": appointment.version,
    })




# Frontend views

def patient_portal(request):
    
    # The assignment does not require real authentication, so the first
    # seeded patient is used for the patient portal.
    patient = Patient.objects.first()

    appointments = Appointment.objects.filter(patient=patient).select_related("provider").order_by("scheduled_at")

    if request.method == "POST":

        try:
            appointment = create_appointment(
                patient=patient,
                provider=Provider.objects.first(),
                appointment_type=request.POST["appointment_type"],
                scheduled_at=request.POST["scheduled_at"],
            )
        except ValueError as exc:
            return render(
                request,
                "patient.html",
                {
                    "appointments": appointments,
                    "error": str(exc),
                },
                status=409,
            )
        
        return redirect("patient-portal")

    return render(
        request,
        "patient.html",
        {
            "appointments": appointments,
        },
    )

@csrf_exempt
def patient_cancel(request, appointment_id):

    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405,
        )

    try:
        cancel_appointment(
            appointment_id=appointment_id,
            expected_version=int(request.POST["version"]),
            changed_by=request.POST["changed_by"],
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=409,
        )

    return redirect("patient-portal")


def provider_portal(request):

    # The assignment does not require real authentication, so the first
    # seeded provider is used for the provider portal.
    provider = Provider.objects.first()

    appointments = Appointment.objects.filter(provider=provider).select_related("patient").order_by("scheduled_at")

    return render(
        request,
        "provider.html",
        {
            "appointments": appointments,
        },
    )

@csrf_exempt
def provider_confirm(request, appointment_id):

    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405,
        )

    try:
        confirm_appointment(
            appointment_id=appointment_id,
            expected_version=int(request.POST["version"]),
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=409,
        )

    return redirect("provider-portal")

@csrf_exempt
def provider_reschedule(request, appointment_id):

    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405,
        )

    try:
        reschedule_appointment(
            appointment_id=appointment_id,
            expected_version=int(request.POST["version"]),
            new_scheduled_at=request.POST["scheduled_at"],
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=409,
        )

    return redirect("provider-portal")