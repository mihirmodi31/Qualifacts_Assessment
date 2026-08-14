from django.urls import path

from . import views


urlpatterns = [
    path("", views.appointment_list, name="appointment-list"),

    # API endpoints
    path("<int:appointment_id>/confirm/", views.appointment_confirm, name="appointment-confirm"),
    path("<int:appointment_id>/reschedule/", views.appointment_reschedule, name="appointment-reschedule"),
    path("<int:appointment_id>/cancel/", views.appointment_cancel, name="appointment-cancel"),

    # Patient and provider frontend views
    path("patient/", views.patient_portal, name="patient-portal"),
    path("provider/", views.provider_portal, name="provider-portal"),
    path("<int:appointment_id>/patient-cancel/", views.patient_cancel, name="patient-cancel"),
    path("<int:appointment_id>/provider-confirm/", views.provider_confirm, name="provider-confirm"),
    path("<int:appointment_id>/provider-reschedule/", views.provider_reschedule, name="provider-reschedule"),
]