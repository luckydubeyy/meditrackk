import os
import pickle
import pandas as pd
from django.conf import settings

_model = None
_symptoms = None

def load_ml_model():
    global _model, _symptoms
    model_path = os.path.join(settings.BASE_DIR, 'ml_model.pkl')
    if os.path.exists(model_path):
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
            _model = data['model']
            _symptoms = data['symptoms']
    return _model, _symptoms

def predict_disease(selected_symptom_names, return_confidence=False):
    model, symptoms = load_ml_model()
    if not model or not symptoms:
        if return_confidence:
            return "Unknown Condition", 0.0
        return "Unknown Condition"

    # Create vector
    row = {symptom: [1 if symptom in selected_symptom_names else 0] for symptom in symptoms}
    df = pd.DataFrame(row)
    prediction = model.predict(df)[0]

    confidence = 85.0  # sensible default if proba isn't available
    if hasattr(model, 'predict_proba'):
        try:
            probabilities = model.predict_proba(df)[0]
            max_prob = float(max(probabilities))
            confidence = round(max_prob * 100, 1)
            # If all 0s were passed, confidence might be low or ambiguous
            if sum(row[s][0] for s in symptoms) == 0:
                confidence = 30.0
        except Exception:
            confidence = 80.0

    if return_confidence:
        return prediction, confidence
    return prediction

def predict_disease_with_confidence(selected_symptom_names):
    return predict_disease(selected_symptom_names, return_confidence=True)

