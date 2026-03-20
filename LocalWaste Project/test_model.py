import pandas as pd
import joblib
from sklearn.metrics import accuracy_score, classification_report
import os

# --- Load test CSV ---
test_file = 'LocalWaste Project/submissions_test.csv'
if not os.path.exists(test_file):
    raise FileNotFoundError(f"{test_file} not found.")

df = pd.read_csv(test_file)

# --- Load model & encoders ---
clf = joblib.load('LocalWaste Project/waste_model.pkl')
le_user = joblib.load('LocalWaste Project/encoder_user.pkl')
le_collector = joblib.load('LocalWaste Project/encoder_collector.pkl')
le_waste = joblib.load('LocalWaste Project/encoder_waste.pkl')

# --- Filter test data to known encoder classes ---
df = df[df['user_id'].isin(le_user.classes_)]
df = df[df['collector_id'].isin(le_collector.classes_)]
df = df[df['waste_type'].isin(le_waste.classes_)]

# --- Encode features ---
df['user_id_enc'] = le_user.transform(df['user_id'])
df['collector_id_enc'] = le_collector.transform(df['collector_id'])
df['waste_type_enc'] = le_waste.transform(df['waste_type'])
df['status_enc'] = df['status'].map({'Proper':1,'Improper':0})

X_test = df[['user_id_enc','collector_id_enc','waste_type_enc','quantity']]
y_test = df['status_enc']

# --- Predict & Evaluate ---
y_pred = clf.predict(X_test)

acc = accuracy_score(y_test, y_pred)
print(f"✅ Test Accuracy: {acc*100:.2f}%")
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))
