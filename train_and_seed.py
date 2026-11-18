import os
import django
import pickle
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User, DoctorProfile, PatientProfile, Symptom, Disease, Medicine

# Define symptoms
symptoms_list = [
    "Fever", "Cough", "Headache", "Fatigue", "Sore Throat", 
    "Shortness of Breath", "Nausea", "Vomiting", "Muscle Ache", 
    "Loss of Taste", "Diarrhea", "Runny Nose", "Chills", 
    "Chest Pain", "Dizziness", "Sneezing", "Stomach Cramps"
]

# Define diseases and characteristic symptoms
disease_data = {
    "Common Cold": ["Sneezing", "Runny Nose", "Sore Throat", "Cough", "Fatigue"],
    "Flu (Influenza)": ["Fever", "Muscle Ache", "Fatigue", "Headache", "Cough", "Chills"],
    "COVID-19": ["Fever", "Cough", "Shortness of Breath", "Loss of Taste", "Fatigue"],
    "Migraine": ["Headache", "Nausea", "Dizziness"],
    "Gastroenteritis": ["Nausea", "Vomiting", "Diarrhea", "Stomach Cramps", "Fever"],
    "Bronchitis": ["Cough", "Chest Pain", "Fatigue", "Fever", "Shortness of Breath"]
}

# Create training dataset
data = []
for disease, d_symptoms in disease_data.items():
    # Base case
    row = {symptom: (1 if symptom in d_symptoms else 0) for symptom in symptoms_list}
    row['disease'] = disease
    data.append(row)
    
    # Variations (missing one symptom)
    for s in d_symptoms:
        variant = row.copy()
        variant[s] = 0
        data.append(variant)

df = pd.DataFrame(data)
X = df[symptoms_list]
y = df['disease']

model = DecisionTreeClassifier()
model.fit(X, y)

# Save model and symptoms list
with open('ml_model.pkl', 'wb') as f:
    pickle.dump({'model': model, 'symptoms': symptoms_list}, f)

print("ML model trained and saved to ml_model.pkl")

# Seed Database
def seed():
    print("Seeding database...")
    # Symptoms
    for s_name in symptoms_list:
        Symptom.objects.get_or_create(name=s_name)

    # Diseases
    for d_name in disease_data.keys():
        Disease.objects.get_or_create(name=d_name, defaults={'description': f'Information about {d_name}.'})

    # Medicines
    medicines = [
        "Paracetamol 500mg", "Ibuprofen 400mg", "Amoxicillin 500mg", 
        "Cetirizine 10mg", "Cough Syrup (Dextromethorphan)", 
        "Oral Rehydration Salts (ORS)", "Azithromycin 250mg", 
        "Antacid Suspension", "Sumatriptan 50mg"
    ]
    for m_name in medicines:
        Medicine.objects.get_or_create(name=m_name)

    # Users
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@meditrack.local', 'admin123')
        print("Admin user created: admin / admin123")

    if not User.objects.filter(username='doctor1').exists():
        doc_user = User.objects.create_user('doctor1', 'doctor@meditrack.local', 'password123', first_name='John', last_name='Smith', is_doctor=True)
        DoctorProfile.objects.create(user=doc_user, specialization='General Physician')
        print("Doctor user created: doctor1 / password123")

    if not User.objects.filter(username='doctor2').exists():
        doc_user = User.objects.create_user('doctor2', 'doctor2@meditrack.local', 'password123', first_name='Sarah', last_name='Connor', is_doctor=True)
        DoctorProfile.objects.create(user=doc_user, specialization='Internal Medicine')
        print("Doctor user created: doctor2 / password123")

    if not User.objects.filter(username='patient1').exists():
        p_user = User.objects.create_user('patient1', 'patient@meditrack.local', 'password123', first_name='Alice', last_name='Doe', is_patient=True)
        PatientProfile.objects.create(user=p_user, age=28, previous_medical_history='Mild asthma in childhood. No previous surgeries.')
        print("Patient user created: patient1 / password123")
    else:
        p_user = User.objects.get(username='patient1')
        PatientProfile.objects.get_or_create(user=p_user, defaults={'age': 28, 'previous_medical_history': 'Mild asthma in childhood. No previous surgeries.'})

    print("Database seeding completed.")

if __name__ == '__main__':
    seed()
