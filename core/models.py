from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_patient = models.BooleanField(default=False)
    is_doctor = models.BooleanField(default=False)

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=100)

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username} ({self.specialization})"

class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    age = models.PositiveIntegerField(null=True, blank=True)
    previous_medical_history = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Patient: {self.user.get_full_name() or self.user.username} (Age: {self.age})"

class Symptom(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Disease(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Medicine(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class ConsultationCase(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Assigned', 'Assigned'),
        ('Completed', 'Completed'),
    )
    CONFIDENCE_CHOICES = (
        ('high', 'High (≥80%)'),
        ('moderate', 'Moderate (50–79%)'),
        ('low', 'Low (<50%)'),
        ('unknown', 'Unknown'),
    )

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cases')
    assigned_doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_cases')
    symptoms = models.ManyToManyField(Symptom)
    predicted_disease = models.CharField(max_length=100, blank=True, null=True)
    prediction_confidence = models.FloatField(null=True, blank=True, default=0.0)
    ai_confidence_level = models.CharField(max_length=10, choices=CONFIDENCE_CHOICES, default='unknown')
    top_predictions = models.JSONField(null=True, blank=True)   # list of {disease, confidence}
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    # Doctor's response
    actual_diagnosis = models.CharField(max_length=100, blank=True, null=True)
    doctor_notes = models.TextField(blank=True, null=True)
    prescribed_medicines = models.ManyToManyField(Medicine, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Case #{self.id} - {self.patient.username} ({self.status})"

