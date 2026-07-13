import json
import psycopg2

# 1. Database Connection (using localhost or local IP since it runs on the server)
# Ensure password and username are correct
conn = psycopg2.connect(
    host="127.0.0.1", # Or your local server IP
    database="tvtracker",
    user="your_username",
    password="your_secure_password"
)
cursor = conn.cursor()

print("Connected to the database. Starting data import...")

# 2. IMPORT MOVIES
try:
    # Rename your TV Time export file to match this, or change the name below
    with open('tvtime-movies.json', 'r') as f:
        movies = json.load(f)
        for m in movies:
            # Safe data extraction (in case some fields are missing from the JSON)
            ids = m.get("id", {})
            imdb_id = ids.get("imdb")
            tvdb_id = ids.get("tvdb")
            title = m.get("title")
            year = m.get("year")
            is_watched = m.get("is_watched", False)
            watched_at = m.get("watched_at")

            # ON CONFLICT DO NOTHING prevents script failure if the same movie is imported twice
            cursor.execute("""
                INSERT INTO Film (imdb_id, tvdb_id, titolo, anno, is_watched, watched_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (imdb_id) DO NOTHING;
            """, (imdb_id, tvdb_id, title, year, is_watched, watched_at))
    print(f"Successfully imported {len(movies)} movies.")
except FileNotFoundError:
    print("Movies JSON file not found, skipping this step.")

# 3. IMPORT TV SHOWS AND EPISODES
try:
    # Rename your TV Time export file to match this, or change the name below
    with open('tvtime-series.json', 'r') as f:
        series = json.load(f)
        for s in series:
            ids = s.get("id", {})
            tvdb_id = ids.get("tvdb")
            imdb_id = ids.get("imdb")
            title = s.get("title")
            status = s.get("status")

            # Insert the series and retrieve the auto-generated Postgres ID (needed for the episodes)
            cursor.execute("""
                INSERT INTO Serie (imdb_id, tvdb_id, titolo, stato)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (tvdb_id) DO NOTHING
                RETURNING id;
            """, (imdb_id, tvdb_id, title, status))
            
            res = cursor.fetchone()
            if res:
                serie_id = res[0] # Newly inserted series
            else:
                # The series already existed (ON CONFLICT), let's fetch its ID to link the episodes
                cursor.execute("SELECT id FROM Serie WHERE tvdb_id = %s", (tvdb_id,))
                serie_id = cursor.fetchone()[0]

            # Extract all episodes from the seasons
            for season in s.get("seasons", []):
                s_num = season.get("number")
                for ep in season.get("episodes", []):
                    ep_ids = ep.get("id", {})
                    ep_tvdb = ep_ids.get("tvdb")
                    ep_num = ep.get("number")
                    ep_name = ep.get("name")
                    ep_watched = ep.get("is_watched", False)
                    ep_watched_at = ep.get("watched_at")

                    cursor.execute("""
                        INSERT INTO Episodi (serie_id, tvdb_id, stagione, numero_episodio, titolo_episodio, is_watched, watched_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (tvdb_id) DO NOTHING;
                    """, (serie_id, ep_tvdb, s_num, ep_num, ep_name, ep_watched, ep_watched_at))
                    
    print(f"Successfully imported {len(series)} TV Shows and their episodes.")
except FileNotFoundError:
    print("TV Shows JSON file not found, skipping this step.")

# 4. FINAL COMMIT AND CLOSING CONNECTION
conn.commit()
cursor.close()
conn.close()
print("Data successfully committed to the database! Operation complete.")
