import pandas as pd

df = pd.read_csv('processed_movies.csv')
print(f"Total rows in processed_movies.csv: {len(df)}")