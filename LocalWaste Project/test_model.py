import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import os

# --- Load submissions CSV ---
submissions_file = 'submissions_large.csv'
if not os.path.exists(submissions_file):
    raise FileNotFoundError(f"{submissions_file} not found.")

df = pd.read_csv(submissions_file)

# --- Load encoders and model ---
clf = joblib.load('waste_model.pkl')
le_user = joblib.load('encoder_user.pkl')
le_collector = joblib.load('encoder_collector.pkl')
le_waste = joblib.load('encoder_waste.pkl')

# --- Encode features ---
df['user_id_enc'] = le_user.transform(df['user_id'])
df['collector_id_enc'] = le_collector.transform(df['collector_id'].fillna(0))
df['waste_type_enc'] = le_waste.transform(df['waste_type'])
df['status_enc'] = df['status'].map({'Proper':1,'Improper':0})

features = ['user_id_enc','collector_id_enc','waste_type_enc','quantity']
target = 'status_enc'

X = df[features]
y = df[target]

# --- Train/Test split (same as training) ---
_, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# --- Predict ---
y_pred = clf.predict(X_test)

# --- Evaluate ---
acc = accuracy_score(y_test, y_pred)
print(f"✅ Test Accuracy: {acc*100:.2f}%")
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))