import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

DB_CONFIG = {
    "host": "34.42.100.68",
    "user": "root",
    "password": "",
    "database": "hw5-db"
}

def get_sqlalchemy_engine():
    return create_engine(f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}")

# Fetch data from the database
def fetch_data():
    # Fetch relevant columns from the 'requests' table
    engine = get_sqlalchemy_engine()
    query = "SELECT client_ip, client_country, gender, age, is_banned, income FROM requests"
    with engine.connect() as conn:
        data = pd.read_sql(query, conn)
    return data

# Split IP address into four separate segments
def split_ip(data):
    # Fill any missing 'client_ip' values with a default placeholder and split into 4 segments
    data['client_ip'] = data['client_ip'].fillna('0.0.0.0')
    ip_split = data['client_ip'].str.split('.', expand=True).astype(int)
    ip_split.columns = ['ip_segment_1', 'ip_segment_2', 'ip_segment_3', 'ip_segment_4']
    data = data.join(ip_split).drop(columns=['client_ip'])
    return data

# Prepare the data by encoding categorical features and splitting IP segments
def prepare_data(data):
    data = split_ip(data)
    
    label_encoders = {
        "client_country": LabelEncoder(),
        "gender": LabelEncoder(),
        "age": LabelEncoder(),
        "income": LabelEncoder()
    }
    
    for column, encoder in label_encoders.items():
        data[column] = encoder.fit_transform(data[column])
    
    return data, label_encoders

# Train a RandomForest to predict 'client_country' from IP segments
def predict_country_from_ip(data):
    # Create an additional feature 'ip_sum' from the sum of IP segments
    data['ip_sum'] = data[['ip_segment_1', 'ip_segment_2', 'ip_segment_3', 'ip_segment_4']].sum(axis=1)
    X = data[['ip_segment_1', 'ip_segment_2', 'ip_segment_3', 'ip_segment_4', 'ip_sum']]
    y = data['client_country']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=561)
    
    model = RandomForestClassifier(n_estimators=500, max_depth=30, min_samples_split=2, min_samples_leaf=1, class_weight='balanced', random_state=561)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"Model 1 - Predict Country from IP Segments - Accuracy: {accuracy * 100:.2f}%")
    return model, accuracy

# Train a RandomForest to predict 'income' from other fields
def predict_income(data):
    data['ip_sum'] = data[['ip_segment_1', 'ip_segment_2', 'ip_segment_3', 'ip_segment_4']].sum(axis=1)
    features = ['client_country', 'gender', 'age', 'is_banned', 'ip_sum']
    X = data[features]
    y = data['income']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=561)
    
    # Define a pipeline with scaling and RandomForestClassifier
    model = Pipeline([
        ('scaler', StandardScaler()), 
        ('rf', RandomForestClassifier(n_estimators=500, max_depth=20, class_weight='balanced', random_state=561))
    ])
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"Model 2 - Predict Income - Accuracy: {accuracy * 100:.2f}%")
    return model, accuracy

def main():
    print("Fetching Data")
    data = fetch_data()

    print("Preparing Data")
    data, _ = prepare_data(data)
    
    print("Training Model 1 - Predict Country from IP Segments")
    model_country, country_accuracy = predict_country_from_ip(data)
    
    print("Training Model 2 - Predict Income")
    model_income, income_accuracy = predict_income(data)

if __name__ == "__main__":
    main()
