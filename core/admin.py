from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, DoctorProfile, PatientProfile, Symptom, Disease, Medicine, ConsultationCase

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_patient', 'is_doctor')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(DoctorProfile)
admin.site.register(PatientProfile)
admin.site.register(Symptom)
admin.site.register(Disease)
admin.site.register(Medicine)
admin.site.register(ConsultationCase)
