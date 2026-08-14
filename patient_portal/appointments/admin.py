from django.contrib import admin


from .models import (
    Patient,
    Provider,
    Appointment,
    AppointmentHistory,
)

# admin.site.register(Patient)
# admin.site.register(Provider)
# admin.site.register(Appointment)
# admin.site.register(AppointmentHistory)

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "email",
    )


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "email",
    )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "provider",
        "appointment_type",
        "scheduled_at",
        "status",
        "version",
        "created_at",
        "updated_at",
    )


@admin.register(AppointmentHistory)
class AppointmentHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "appointment",
        "action",
        "changed_by",
        "old_status",
        "new_status",
        "old_scheduled_at",
        "new_scheduled_at",
        "created_at",
    )