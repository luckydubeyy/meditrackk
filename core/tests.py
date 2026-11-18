from django.test import TestCase, Client
from django.urls import reverse
from core.models import User, Symptom, Disease, Medicine, ConsultationCase, DoctorProfile, PatientProfile
from core.ml_service import predict_disease, predict_disease_with_confidence

class MediTrackTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Symptoms
        self.s1 = Symptom.objects.create(name="Fever")
        self.s2 = Symptom.objects.create(name="Cough")
        self.s3 = Symptom.objects.create(name="Fatigue")
        
        # Medicines
        self.med1 = Medicine.objects.create(name="Paracetamol 500mg")
        self.med2 = Medicine.objects.create(name="Cough Syrup")

        # Patient
        self.patient = User.objects.create_user(
            username='testpatient', password='password123', is_patient=True
        )
        PatientProfile.objects.create(
            user=self.patient,
            age=29,
            previous_medical_history="Mild asthma in childhood."
        )

        # Doctor
        self.doctor = User.objects.create_user(
            username='testdoctor', password='password123', is_doctor=True
        )
        DoctorProfile.objects.create(user=self.doctor, specialization="General Practice")

    def test_ml_prediction(self):
        # We test with symptoms that likely lead to a prediction
        prediction = predict_disease(["Fever", "Cough"])
        self.assertIsInstance(prediction, str)
        self.assertTrue(len(prediction) > 0)

        # Test prediction with confidence
        pred, conf = predict_disease_with_confidence(["Fever", "Cough"])
        self.assertIsInstance(pred, str)
        self.assertIsInstance(conf, float)
        self.assertGreater(conf, 0.0)

    def test_patient_registration_with_age_and_history(self):
        # Test registering a new patient with age and previous medical history
        res = self.client.post(reverse('register'), {
            'first_name': 'Robert',
            'last_name': 'Smith',
            'username': 'robert_patient',
            'email': 'robert@test.com',
            'password': 'password123',
            'role': 'patient',
            'age': '35',
            'previous_medical_history': 'Hypertension diagnosed in 2022.'
        })
        self.assertEqual(res.status_code, 302)

        user = User.objects.get(username='robert_patient')
        self.assertTrue(user.is_patient)
        self.assertTrue(hasattr(user, 'patient_profile'))
        self.assertEqual(user.patient_profile.age, 35)
        self.assertIn("Hypertension", user.patient_profile.previous_medical_history)

    def test_patient_consultation_flow(self):
        # Login as patient
        self.client.login(username='testpatient', password='password123')

        # Submit new consultation
        response = self.client.post(reverse('new_consultation'), {
            'symptoms': [self.s1.id, self.s2.id]
        })
        self.assertEqual(response.status_code, 302)

        # Verify case created
        case = ConsultationCase.objects.filter(patient=self.patient).first()
        self.assertIsNotNone(case)
        self.assertEqual(case.status, 'Assigned')
        self.assertEqual(case.assigned_doctor, self.doctor)
        self.assertIn(self.s1, case.symptoms.all())
        self.assertGreater(case.prediction_confidence, 0.0)

        # Check detail page
        detail_res = self.client.get(reverse('case_detail', args=[case.id]))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, case.predicted_disease)
        self.assertContains(detail_res, "testpatient")

    def test_doctor_review_flow(self):
        # Create a case manually
        case = ConsultationCase.objects.create(
            patient=self.patient,
            assigned_doctor=self.doctor,
            predicted_disease="Flu (Influenza)",
            prediction_confidence=85.0,
            status="Assigned"
        )
        case.symptoms.add(self.s1, self.s2)

        # Login as doctor
        self.client.login(username='testdoctor', password='password123')

        # Check doctor dashboard
        dash_res = self.client.get(reverse('doctor_dashboard'))
        self.assertEqual(dash_res.status_code, 200)
        self.assertContains(dash_res, "testpatient")

        # Check review page displays patient's age and history
        review_get = self.client.get(reverse('review_case', args=[case.id]))
        self.assertEqual(review_get.status_code, 200)
        self.assertContains(review_get, "29 years")
        self.assertContains(review_get, "Mild asthma in childhood")

        # Submit review
        review_res = self.client.post(reverse('review_case', args=[case.id]), {
            'actual_diagnosis': 'Mild Viral Infection',
            'doctor_notes': 'Drink warm fluids and take rest for 3 days.',
            'medicines': [self.med1.id, self.med2.id]
        })
        self.assertEqual(review_res.status_code, 302)

        # Reload case and verify
        case.refresh_from_db()
        self.assertEqual(case.status, 'Completed')
        self.assertEqual(case.actual_diagnosis, 'Mild Viral Infection')
        self.assertEqual(case.prescribed_medicines.count(), 2)

    def test_nearby_places_api(self):
        # Test hospital query
        hosp_res = self.client.get(reverse('nearby_places_api'), {'type': 'hospital', 'lat': '40.7128', 'lon': '-74.0060'})
        self.assertEqual(hosp_res.status_code, 200)
        hosp_data = hosp_res.json()
        self.assertEqual(hosp_data['status'], 'success')
        self.assertEqual(hosp_data['type'], 'hospital')
        self.assertGreater(len(hosp_data['results']), 0)
        self.assertIn('name', hosp_data['results'][0])
        self.assertIn('address', hosp_data['results'][0])

        # Test pharmacy query
        pharm_res = self.client.get(reverse('nearby_places_api'), {'type': 'pharmacy', 'query': 'Boston'})
        self.assertEqual(pharm_res.status_code, 200)
        pharm_data = pharm_res.json()
        self.assertEqual(pharm_data['status'], 'success')
        self.assertEqual(pharm_data['type'], 'pharmacy')
        self.assertGreater(len(pharm_data['results']), 0)
