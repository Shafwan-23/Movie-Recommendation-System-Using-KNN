import pandas as pd
import ast

df = pd.read_csv("tmdb_5000_movies.csv")

df = df[['id', 'title', 'genres', 'overview', 'vote_average', 'vote_count', 'popularity']]

df.dropna(subset=['title', 'genres'], inplace=True)

def get_primary_genre(genre_str):
    try:
        genres = ast.literal_eval(genre_str)
        if genres:
            return genres[0]['name']
        else:
            return None
    except:
        return None

df['genre'] = df['genres'].apply(get_primary_genre)

df = df[df['genre'].notnull()]

df.drop(columns=['genres'], inplace=True)

df.reset_index(drop=True, inplace=True)

df.to_csv("processed_movies.csv", index=False)

print("✅ Preprocessing done. Each movie now has one genre. Saved as 'processed_movies.csv'")
