import pandas as pd
import MySQLdb
from db_config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

try:
    df = pd.read_csv('processed_movies.csv')
except Exception as e:
    print(f"Error loading CSV: {e}")
    exit(1)


print(f"Total rows in CSV: {len(df)}")

print("\nNaN counts in each column:")
print(df.isna().sum())


duplicate_ids = df[df['id'].duplicated(keep=False)]
if not duplicate_ids.empty:
    print("\nDuplicate ID values found:")
    print(duplicate_ids[['id', 'title']])


df['title'] = df['title'].fillna('Unknown Title')
df['overview'] = df['overview'].fillna('No overview available')
df['genre'] = df['genre'].fillna('Unknown')


if df['id'].isna().any():
    print("\nRows with NaN in 'id':")
    print(df[df['id'].isna()])
    df = df.dropna(subset=['id'])
    print(f"Rows after dropping NaN in 'id': {len(df)}")


try:
    df['id'] = df['id'].astype(int)
except ValueError as e:
    print(f"Error converting 'id' to integer: {e}")
    exit(1)


print("\nFirst 5 rows after cleaning:")
print(df.head())

try:
    conn = MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASSWORD, db=MYSQL_DB)
    cursor = conn.cursor()
except Exception as e:
    print(f"Error connecting to MySQL: {e}")
    exit(1)

inserted_count = 0
for index, row in df.iterrows():
    try:
        cursor.execute('INSERT INTO movies (id, title, overview, genre) VALUES (%s, %s, %s, %s)',
                       (row['id'], row['title'], row['overview'], row['genre']))
        inserted_count += 1
    except MySQLdb.Error as e:
        print(f"Error inserting row {index} (id={row['id']}): {row.to_dict()}")
        print(f"MySQL Error: {e}")

conn.commit()
cursor.close()
conn.close()
print(f"\nMovies inserted into database: {inserted_count}")
print(f"Expected insertions: {len(df)}")