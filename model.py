import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import numpy as np

df = pd.read_csv('processed_movies.csv')
numerical_features = ['vote_average', 'vote_count', 'popularity']
genres = df['genre'].str.get_dummies(',')
features = pd.concat([df[numerical_features], genres], axis=1)

scaler = StandardScaler()
features[numerical_features] = scaler.fit_transform(features[numerical_features])

y = df['id'].astype(str) 
X_train, _, y_train, _ = train_test_split(features, y, test_size=0.2, random_state=42)

knn = KNeighborsClassifier(n_neighbors=20)
knn.fit(X_train, y_train)

joblib.dump(knn, 'knn_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
df[['id', 'title', 'overview', 'genre']].to_pickle('movies.pkl')
features.to_pickle('features.pkl')

print("Model and data saved successfully.")