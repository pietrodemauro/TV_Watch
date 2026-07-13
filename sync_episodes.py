import psycopg2
import requests
import time
from datetime import datetime

# --- CONFIGURATION ---
OMDB_API_KEY = "YOUR_OMDB_API_KEY"
DB_HOST = "127.0.0.1" 
DB_USER = "your_username"
DB_PASS = "your_secure_password"
DB_NAME = "tvtracker"

def get_db():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

def sync_series():
    oggi = datetime.now()
    # In Python, weekday() 0 is Monday, 6 is Sunday
    is_domenica = oggi.weekday() == 6 
    
    print(f"\n[{oggi.strftime('%Y-%m-%d %H:%M:%S')}] Starting sync process...")
    
    conn = get_db()
    cur = conn.cursor()

    # LOGIC: Deep Scan on Sundays, otherwise check only "Continuing" shows
    if is_domenica:
        print("DEEP SCAN: Checking ALL series (including Ended ones)...")
        cur.execute("SELECT id, imdb_id, titolo FROM Serie;")
    else:
        print("Standard Scan: Checking only 'Continuing' series...")
        cur.execute("SELECT id, imdb_id, titolo FROM Serie WHERE stato = 'Continuing';")
        
    series_to_update = cur.fetchall()
    print(f"Found {len(series_to_update)} series to analyze.")

    for s in series_to_update:
        serie_id, imdb_id, titolo = s
        
        if not imdb_id:
            continue

        url_main = f"http://www.omdbapi.com/?i={imdb_id}&type=series&apikey={OMDB_API_KEY}"
        try:
            res_main = requests.get(url_main).json()
            if res_main.get("Response") == "False":
                continue

            total_seasons = int(res_main.get("totalSeasons", 0))
            
            # Evaluate status catching standard dashes and typography en-dashes
            year_str = res_main.get("Year", "").strip()
            if year_str.endswith("-") or year_str.endswith("–"):
                new_status = "Continuing"
            else:
                new_status = "Ended"
            
            # Update status dynamically
            cur.execute("UPDATE Serie SET stato = %s WHERE id = %s", (new_status, serie_id))

            # API OPTIMIZATION: Start checking from the maximum season we already have
            cur.execute("SELECT MAX(stagione) FROM Episodi WHERE serie_id = %s", (serie_id,))
            max_season_db = cur.fetchone()[0]
            if max_season_db is None:
                max_season_db = 1

            # Get existing episodes for the seasons we are scanning
            cur.execute("SELECT stagione, numero_episodio FROM Episodi WHERE serie_id = %s AND stagione >= %s", (serie_id, max_season_db))
            existing_episodes = set((row[0], row[1]) for row in cur.fetchall())

            episodi_aggiunti = 0

            for season in range(max_season_db, total_seasons + 1):
                url_season = f"http://www.omdbapi.com/?i={imdb_id}&Season={season}&apikey={OMDB_API_KEY}"
                res_season = requests.get(url_season).json()
                
                if res_season.get("Response") == "True":
                    for ep in res_season.get("Episodes", []):
                        ep_num = int(ep.get("Episode"))
                        ep_title = ep.get("Title")
                        
                        if (season, ep_num) not in existing_episodes:
                            cur.execute("""
                                INSERT INTO Episodi (serie_id, stagione, numero_episodio, titolo_episodio)
                                VALUES (%s, %s, %s, %s)
                            """, (serie_id, season, ep_num, ep_title))
                            episodi_aggiunti += 1
                            print(f"[{titolo}] New Episode: S{season:02d}xE{ep_num:02d} - {ep_title}")
                
                time.sleep(0.1) # Rate limiting
            
            conn.commit()

        except Exception as e:
            print(f"Error checking {titolo}: {e}")
            conn.rollback()
        
        time.sleep(0.2)

    cur.close()
    conn.close()
    print("Sync process completed!\n")

if __name__ == "__main__":
    if OMDB_API_KEY == "YOUR_OMDB_API_KEY":
        print("ERROR: Insert your OMDB API KEY!")
        exit(1)
    sync_series()
