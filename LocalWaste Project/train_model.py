import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# --- Load submissions CSV ---
submissions_file = 'submissions_large.csv'
if not os.path.exists(submissions_file):
    raise FileNotFoundError(f"{submissions_file} not found.")

df = pd.read_csv(submissions_file)

# --- Encode categorical features ---
le_user = LabelEncoder()
le_collector = LabelEncoder()
le_waste = LabelEncoder()

df['user_id_enc'] = le_user.fit_transform(df['user_id'])
df['collector_id_enc'] = le_collector.fit_transform(df['collector_id'].fillna(0))
df['waste_type_enc'] = le_waste.fit_transform(df['waste_type'])
df['status_enc'] = df['status'].map({'Proper':1,'Improper':0})

# --- Features and target ---
features = ['user_id_enc','collector_id_enc','waste_type_enc','quantity']
target = 'status_enc'

X = df[features]
y = df[target]

# --- Train/Test split ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# --- Train model ---
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# --- Save trained model and encoders ---
joblib.dump(clf, 'waste_model.pkl')
joblib.dump(le_user, 'encoder_user.pkl')
joblib.dump(le_collector, 'encoder_collector.pkl')
joblib.dump(le_waste, 'encoder_waste.pkl')

print("✅ Model trained and saved successfully!")
print(f"Training samples: {X_train.shape[0]}, Test samples: {X_test.shape[0]}")