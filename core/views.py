import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import User, DoctorProfile, PatientProfile, Symptom, Disease, Medicine, ConsultationCase
from .ml_service import predict_disease

def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_doctor:
            return redirect('doctor_dashboard')
        return redirect('patient_dashboard')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            if user.is_doctor:
                return redirect('doctor_dashboard')
            elif user.is_patient:
                return redirect('patient_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        fn = request.POST.get('first_name', '').strip()
        ln = request.POST.get('last_name', '').strip()
        u = request.POST.get('username', '').strip()
        e = request.POST.get('email', '').strip()
        p = request.POST.get('password', '').strip()
        role = request.POST.get('role', 'patient')
        spec = request.POST.get('specialization', '').strip()
        age = request.POST.get('age', '').strip()
        previous_medical_history = request.POST.get('previous_medical_history', '').strip()

        if User.objects.filter(username=u).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'register.html')

        age_val = None
        if role != 'doctor' and age:
            try:
                age_val = int(age)
                if age_val <= 0 or age_val > 125:
                    messages.error(request, "Please enter a valid positive age (1-125).")
                    return render(request, 'register.html')
            except ValueError:
                messages.error(request, "Age must be a valid number.")
                return render(request, 'register.html')

        user = User.objects.create_user(
            username=u, email=e, password=p, first_name=fn, last_name=ln
        )

        if role == 'doctor':
            user.is_doctor = True
            user.save()
            DoctorProfile.objects.create(user=user, specialization=spec or 'General Practice')
        else:
            user.is_patient = True
            user.save()
            PatientProfile.objects.create(
                user=user,
                age=age_val,
                previous_medical_history=previous_medical_history
            )

        login(request, user)
        messages.success(request, "Account created successfully!")
        if user.is_doctor:
            return redirect('doctor_dashboard')
        return redirect('patient_dashboard')

    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')

@login_required
def patient_dashboard(request):
    if not request.user.is_patient and not request.user.is_superuser:
        messages.error(request, "Access restricted to patients.")
        return redirect('home')

    patient_profile = getattr(request.user, 'patient_profile', None)
    cases = ConsultationCase.objects.filter(patient=request.user).order_by('-created_at')
    return render(request, 'patient_dashboard.html', {
        'cases': cases,
        'patient_profile': patient_profile
    })

@login_required
def new_consultation(request):
    if not request.user.is_patient and not request.user.is_superuser:
        messages.error(request, "Access restricted to patients.")
        return redirect('home')

    symptoms = Symptom.objects.all().order_by('name')

    if request.method == 'POST':
        symptom_ids = request.POST.getlist('symptoms')
        if not symptom_ids:
            messages.error(request, "Please select at least one symptom.")
            return render(request, 'new_consultation.html', {'symptoms': symptoms})

        selected_symptoms = Symptom.objects.filter(id__in=symptom_ids)
        symptom_names = [s.name for s in selected_symptoms]

        # ML Prediction with confidence score
        predicted_disease, confidence = predict_disease(symptom_names, return_confidence=True)

        # Doctor Assignment (Random or Available)
        doctors = User.objects.filter(is_doctor=True)
        assigned_doctor = random.choice(doctors) if doctors.exists() else None

        case = ConsultationCase.objects.create(
            patient=request.user,
            assigned_doctor=assigned_doctor,
            predicted_disease=predicted_disease,
            prediction_confidence=confidence,
            status='Assigned' if assigned_doctor else 'Pending'
        )
        case.symptoms.set(selected_symptoms)

        messages.success(request, f"Case submitted! Preliminary prediction: {predicted_disease} ({confidence}% confidence)")
        return redirect('case_detail', case_id=case.id)

    return render(request, 'new_consultation.html', {'symptoms': symptoms})

@login_required
def case_detail(request, case_id):
    case = get_object_or_404(ConsultationCase, id=case_id)
    # Check access permission
    if not request.user.is_superuser and case.patient != request.user and case.assigned_doctor != request.user:
        messages.error(request, "You do not have permission to view this case.")
        return redirect('home')

    patient_profile = getattr(case.patient, 'patient_profile', None)
    return render(request, 'case_detail.html', {
        'case': case,
        'patient_profile': patient_profile
    })

@login_required
def doctor_dashboard(request):
    if not request.user.is_doctor and not request.user.is_superuser:
        messages.error(request, "Access restricted to doctors.")
        return redirect('home')

    cases = ConsultationCase.objects.filter(assigned_doctor=request.user).select_related('patient', 'patient__patient_profile').order_by('-created_at')
    return render(request, 'doctor_dashboard.html', {'cases': cases})

@login_required
def review_case(request, case_id):
    if not request.user.is_doctor and not request.user.is_superuser:
        messages.error(request, "Access restricted to doctors.")
        return redirect('home')

    case = get_object_or_404(ConsultationCase, id=case_id)
    if not request.user.is_superuser and case.assigned_doctor != request.user:
        messages.error(request, "You are not assigned to review this case.")
        return redirect('doctor_dashboard')

    patient_profile = getattr(case.patient, 'patient_profile', None)
    medicines = Medicine.objects.all().order_by('name')

    if request.method == 'POST':
        case.actual_diagnosis = request.POST.get('actual_diagnosis')
        case.doctor_notes = request.POST.get('doctor_notes')
        case.status = 'Completed'
        case.save()

        medicine_ids = request.POST.getlist('medicines')
        if medicine_ids:
            case.prescribed_medicines.set(Medicine.objects.filter(id__in=medicine_ids))
        else:
            case.prescribed_medicines.clear()

        messages.success(request, "Consultation and prescription updated successfully!")
        return redirect('doctor_dashboard')

    return render(request, 'review_case.html', {
        'case': case,
        'patient_profile': patient_profile,
        'medicines': medicines
    })

def nearby_places_api(request):
    place_type = request.GET.get('type', 'hospital').lower()
    query = request.GET.get('query', '').strip()
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')

    location_label = query if query else ("your current area" if (lat and lon) else "Central District")

    if place_type == 'pharmacy':
        facilities = [
            {
                "name": "Apollo Pharmacy 24/7",
                "address": f"Plot 12, Healthcare Blvd, near {location_label}",
                "distance": "0.4 km away",
                "phone": "+1 (800) 555-0144",
                "status": "Open 24 Hours",
                "is_open": True,
                "map_url": f"https://www.google.com/maps/search/?api=1&query=Apollo+Pharmacy+{location_label}"
            },
            {
                "name": "MedPlus Chemist & Druggist",
                "address": f"45 Market Street, Central Square, {location_label}",
                "distance": "0.9 km away",
                "phone": "+1 (800) 555-0182",
                "status": "Open now • Closes 11:00 PM",
                "is_open": True,
                "map_url": f"https://www.google.com/maps/search/?api=1&query=MedPlus+Pharmacy+{location_label}"
            },
            {
                "name": "Wellness Forever Life Care",
                "address": f"Shop 8, Crossroad Avenue, {location_label}",
                "distance": "1.5 km away",
                "phone": "+1 (800) 555-0199",
                "status": "Open 24 Hours",
                "is_open": True,
                "map_url": f"https://www.google.com/maps/search/?api=1&query=Pharmacy+{location_label}"
            },
            {
                "name": "CareFirst Community Pharmacy",
                "address": f"102 Westside Clinic Road, {location_label}",
                "distance": "2.1 km away",
                "phone": "+1 (800) 555-0131",
                "status": "Open now • Closes 10:00 PM",
                "is_open": True,
                "map_url": f"https://www.google.com/maps/search/?api=1&query=Community+Pharmacy+{location_label}"
            }
        ]
    else:
        facilities = [
            {
                "name": "City General Hospital & Emergency Trauma Care",
                "address": f"100 Medical Enclave, Main Arterial Road, {location_label}",
                "distance": "0.7 km away",
                "phone": "+1 (800) 555-0100 (Emergency: 911 / 112)",
                "status": "Open 24/7 (Emergency & ICU Ready)",
                "is_open": True,
                "map_url": f"https://www.google.com/maps/search/?api=1&query=Hospital+{location_label}"
            },
            {
                "name": "St. Jude Multi-Speciality Medical Center",
                "address": f"77 Healing Way, Sector 4, {location_label}",
                "distance": "1.3 km away",
                "phone": "+1 (800) 555-0125",
                "status": "Open 24/7",
                "is_open": True,
                "map_url": f"https://www.google.com/maps/search/?api=1&query=Medical+Center+{location_label}"
            },
            {
                "name": "Metro Life Care Hospital",
                "address": f"240 Ring Road Bypass, {location_label}",
                "distance": "2.4 km away",
                "phone": "+1 (800) 555-0170",
                "status": "Open 24/7",
                "is_open": True,
                "map_url": f"https://www.google.com/maps/search/?api=1&query=Metro+Hospital+{location_label}"
            },
            {
                "name": "Sunrise Charitable Hospital & Clinic",
                "address": f"15 North Avenue, {location_label}",
                "distance": "3.2 km away",
                "phone": "+1 (800) 555-0163",
                "status": "Open • OPD Closes 9:00 PM",
                "is_open": True,
                "map_url": f"https://www.google.com/maps/search/?api=1&query=Clinic+{location_label}"
            }
        ]

    return JsonResponse({
        "status": "success",
        "type": place_type,
        "location": location_label,
        "results": facilities
    })
