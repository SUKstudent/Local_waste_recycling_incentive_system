import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# --- Correct path to train CSV ---
train_file = os.path.join('LocalWaste Project', 'submissions_train.csv')
if not os.path.exists(train_file):
    raise FileNotFoundError(f"{train_file} not found.")

df = pd.read_csv(train_file)

# --- Encode categorical features ---
le_user = LabelEncoder()
le_collector = LabelEncoder()
le_waste = LabelEncoder()

df['user_id_enc'] = le_user.fit_transform(df['user_id'])
df['collector_id_enc'] = le_collector.fit_transform(df['collector_id'].fillna(0))
df['waste_type_enc'] = le_waste.fit_transform(df['waste_type'])
df['status_enc'] = df['status'].map({'Proper':1,'Improper':0})

# --- Features & target ---
X = df[['user_id_enc','collector_id_enc','waste_type_enc','quantity']]
y = df['status_enc']

# --- Train model ---
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X, y)

# --- Save model & encoders ---
joblib.dump(clf, os.path.join('LocalWaste Project','waste_model.pkl'))
joblib.dump(le_user, os.path.join('LocalWaste Project','encoder_user.pkl'))
joblib.dump(le_collector, os.path.join('LocalWaste Project','encoder_collector.pkl'))
joblib.dump(le_waste, os.path.join('LocalWaste Project','encoder_waste.pkl'))

print("✅ Model trained and saved!")
print(f"Training samples: {X.shape[0]}")
