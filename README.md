# Medi Track – Medical Software Assistant

Medi Track is an intelligent healthcare web application prototype designed to streamline patient triage and doctor consultations. Patients can report their symptoms to receive an instant machine-learning based preliminary disease prediction, get automatically matched with a licensed doctor, and view digital instructions and prescriptions.

---

## 🌟 Key Features

### 1. Patient Portal
- **Registration & Authentication**: Simple patient account creation.
- **Symptom Checker**: Select present symptoms from a structured catalog.
- **ML Disease Prediction**: Instant AI-based assessment providing preliminary health guidance.
- **Automated Doctor Matching**: Assigns the consultation case to an available doctor.
- **Case Tracking & Prescriptions**: View real-time status, doctor instructions, and prescribed medications.

### 2. Doctor Portal
- **Dashboard**: Track all assigned patient consultation requests.
- **Case Review**: Inspect reported symptoms, patient history, and the preliminary ML prediction.
- **Clinical Evaluation**: Confirm/adjust diagnoses, write detailed medical advice, and prescribe specific medicines.

### 3. Administrator Panel
- **Django Admin Interface**: Full CRUD access to manage Patients, Doctors, Symptoms, Diseases, and Medicines.
- **Doctor Assignment Management**: Re-assign cases or manage doctor specializations.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure you have Python 3.10+ installed.

### 2. Setup Virtual Environment & Dependencies
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Seed Database & Train ML Model
The project comes with a seed script that creates sample medical data (symptoms, diseases, medicines) and default accounts:
```bash
python train_and_seed.py
```

### 4. Run the Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 🔑 Demo Credentials

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Doctor** | `doctor1` | `password123` | General Physician |
| **Doctor** | `doctor2` | `password123` | Internal Medicine |
| **Patient** | `patient1` | `password123` | Pre-registered patient |
| **Admin** | `admin` | `admin123` | Django Admin (`/admin`) |

---

## 🔬 Machine Learning Model
The ML component is implemented using `scikit-learn` (Decision Tree Classifier) in `core/ml_service.py`. It evaluates binary symptom feature vectors against learned disease profiles to provide real-time suggestions.

> **Disclaimer**: This is an academic prototype intended for demonstration and educational purposes only. It should not be used as a real-world medical diagnostic tool.
