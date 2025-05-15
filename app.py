from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import bcrypt
import pandas as pd
import joblib
import numpy as np
from db_config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

app = Flask(__name__)
app.secret_key = 'x7k9m2p8q3z5w1r4t6y0u2j8h5n3b6v'


app.config['MYSQL_HOST'] = MYSQL_HOST
app.config['MYSQL_USER'] = MYSQL_USER
app.config['MYSQL_PASSWORD'] = MYSQL_PASSWORD
app.config['MYSQL_DB'] = MYSQL_DB

mysql = MySQL(app)


knn = joblib.load('knn_model.pkl')
scaler = joblib.load('scaler.pkl')
movies_df = pd.read_pickle('movies.pkl')
features_df = pd.read_pickle('features.pkl')

GENRES = [
    'Action', 'Adventure', 'Fantasy', 'Animation', 'Science Fiction',
    'Drama', 'Thriller', 'Family', 'Comedy', 'History', 'Western',
    'Documentary', 'Crime', 'Horror', 'Music', 'Romance', 'Mystery',
    'Foreign', 'War'
]

def get_recommendations(user_id, genres=None):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT movie_id FROM user_interactions WHERE user_id = %s AND interaction_type = %s', (user_id, 'like'))
    liked_movies = cursor.fetchall()
    cursor.close()

  
    recommendations_df = movies_df.copy()


    if genres:
        recommendations_df = recommendations_df[
            recommendations_df['genre'].apply(lambda x: any(g in x.split(',') for g in genres))
        ]
        if recommendations_df.empty:
            print("No movies found for selected genres:", genres)
            return []

    if not liked_movies:
    
        recommendations = recommendations_df.sort_values('id').head(5).to_dict('records')
        print("Recommended movie IDs (no interactions):", [m['id'] for m in recommendations])
        return recommendations


    liked_movie_ids = [m['movie_id'] for m in liked_movies]
    liked_features = features_df.loc[movies_df['id'].isin(liked_movie_ids)]

    if liked_features.empty:
        recommendations = recommendations_df.sort_values('id').head(5).to_dict('records')
        print("Recommended movie IDs (empty features):", [m['id'] for m in recommendations])
        return recommendations

    _, indices = knn.kneighbors(liked_features, n_neighbors=20)
    recommended_movie_ids = movies_df.iloc[np.unique(indices.flatten())]['id']
    recommendations = recommendations_df[recommendations_df['id'].isin(recommended_movie_ids)].to_dict('records')
    print("Recommended movie IDs (KNN):", [m['id'] for m in recommendations])
    return recommendations

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    
    selected_genres = request.args.getlist('genres')
    if selected_genres:
        selected_genres = [g for g in selected_genres if g in GENRES]
    else:
        selected_genres = []  

    recommendations = get_recommendations(session['user_id'], genres=selected_genres or None)
    return render_template('index.html', recommendations=recommendations, genres=GENRES, selected_genres=selected_genres)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        cursor = mysql.connection.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, hashed_password))
            mysql.connection.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except MySQLdb.IntegrityError:
            flash('Username already exists.', 'error')
        finally:
            cursor.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()

        if user and bcrypt.checkpw(password, user['password'].encode('utf-8')):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/like/<int:movie_id>')
def like_movie(movie_id):
    if 'user_id' not in session:
        flash('Please log in to like movies.', 'error')
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    try:
        cursor.execute('SELECT id FROM movies WHERE id = %s', (movie_id,))
        if not cursor.fetchone():
            flash('Movie not found.', 'error')
            return redirect(url_for('index'))

        cursor.execute('INSERT INTO user_interactions (user_id, movie_id, interaction_type) VALUES (%s, %s, %s)',
                       (session['user_id'], movie_id, 'like'))
        mysql.connection.commit()
        flash('Movie liked!', 'success')
    except MySQLdb.IntegrityError as e:
        flash('Error liking movie. Please try again.', 'error')
        print(f"IntegrityError: {e}")
    finally:
        cursor.close()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT m.* FROM movies m JOIN user_interactions ui ON m.id = ui.movie_id WHERE ui.user_id = %s AND ui.interaction_type = %s',
                   (session['user_id'], 'like'))
    liked_movies = cursor.fetchall()
    cursor.close()
    return render_template('profile.html', liked_movies=liked_movies)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    query = request.args.get('query', '').strip()
    if not query:
        flash('Please enter a search term.', 'error')
        return redirect(url_for('index'))

    search_results = movies_df[movies_df['title'].str.contains(query, case=False, na=False)].to_dict('records')
    if not search_results:
        flash('No movies found matching your search.', 'error')
        return redirect(url_for('index'))

    return render_template('search_results.html', search_results=search_results, query=query)


if __name__ == '__main__':
    app.run(debug=True)