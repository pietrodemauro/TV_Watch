import json
import psycopg2

# 1. Connessione al Database (usiamo localhost o l'IP locale perché siamo sul server)
# Assicurati che password e utente siano quelli corretti
conn = psycopg2.connect(
    host="127.0.0.1", # Oppure 192.168.1.17
    database="tvtracker",
    user="Pietro",
    password="Ugo_Ugazzi3"
)
cursor = conn.cursor()

print("Connesso al database. Inizio l'importazione...")

# 2. IMPORTAZIONE FILM
try:
    with open('tvtime-movies-2026-07-04.json', 'r') as f:
        movies = json.load(f)
        for m in movies:
            # Estrazione sicura dei dati (in caso manchino dei campi nel JSON)
            ids = m.get("id", {})
            imdb_id = ids.get("imdb")
            tvdb_id = ids.get("tvdb")
            title = m.get("title")
            year = m.get("year")
            is_watched = m.get("is_watched", False)
            watched_at = m.get("watched_at")

            # ON CONFLICT DO NOTHING evita che lo script si blocchi se importi due volte lo stesso film
            cursor.execute("""
                INSERT INTO Film (imdb_id, tvdb_id, titolo, anno, is_watched, watched_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (imdb_id) DO NOTHING;
            """, (imdb_id, tvdb_id, title, year, is_watched, watched_at))
    print(f"Importati {len(movies)} Film.")
except FileNotFoundError:
    print("File dei film non trovato, salto il passaggio.")

# 3. IMPORTAZIONE SERIE E EPISODI
try:
    with open('tvtime-series-2026-07-04.json', 'r') as f:
        series = json.load(f)
        for s in series:
            ids = s.get("id", {})
            tvdb_id = ids.get("tvdb")
            imdb_id = ids.get("imdb")
            title = s.get("title")
            status = s.get("status")

            # Inserisce la serie e recupera l'ID generato da Postgres (necessario per gli episodi)
            cursor.execute("""
                INSERT INTO Serie (imdb_id, tvdb_id, titolo, stato)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (tvdb_id) DO NOTHING
                RETURNING id;
            """, (imdb_id, tvdb_id, title, status))
            
            res = cursor.fetchone()
            if res:
                serie_id = res[0] # Nuova serie appena inserita
            else:
                # La serie esisteva già (ON CONFLICT), andiamo a pescare il suo ID per collegare gli episodi
                cursor.execute("SELECT id FROM Serie WHERE tvdb_id = %s", (tvdb_id,))
                serie_id = cursor.fetchone()[0]

            # Estrai tutti gli episodi dalle varie stagioni
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
                    
    print(f"Importate {len(series)} Serie TV con i rispettivi episodi.")
except FileNotFoundError:
    print("File delle serie TV non trovato, salto il passaggio.")

# 4. SALVATAGGIO FINALE E CHIUSURA
conn.commit()
cursor.close()
conn.close()
print("Dati scritti fisicamente nel database! Operazione conclusa.")
