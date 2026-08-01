from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import requests
from typing import List

app = FastAPI()

# --- CONFIGURATION ---
OMDB_API_KEY = "YOUR_OMDB_API_KEY"
DB_HOST = "127.0.0.1"
DB_USER = "your_username"
DB_PASS = "your_secure_password"
DB_NAME = "tvtracker"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class AddRequest(BaseModel):
    query: str

class RateRequest(BaseModel):
    voto: int

class CollectionRequest(BaseModel):
    nome: str
    tipo: str

class SyncItemsRequest(BaseModel):
    item_ids: List[int]

def get_db():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

# ==========================================
# MOVIES ENDPOINTS
# ==========================================
@app.get("/api/movies")
def get_movies():
    conn = get_db(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM Film ORDER BY id DESC;")
    movies = cur.fetchall()
    cur.close(); conn.close()
    return jsonable_encoder([dict(m) for m in movies])

@app.post("/api/movies/add")
def add_movie(req: AddRequest):
    param = f"i={req.query}" if req.query.startswith("tt") else f"t={req.query}"
    url = f"http://www.omdbapi.com/?{param}&type=movie&apikey={OMDB_API_KEY}"
    response = requests.get(url).json()
    if response.get("Response") == "False":
        raise HTTPException(status_code=404, detail="Movie not found")
    
    imdb_id = response.get("imdbID")
    titolo = response.get("Title")
    try: anno = int(response.get("Year", "0")[:4]) 
    except: anno = None
    locandina = response.get("Poster")

    conn = get_db(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id FROM Film WHERE imdb_id = %s", (imdb_id,))
    esistente = cur.fetchone()
    if esistente:
        cur.close(); conn.close()
        return {"status": "exists", "id": esistente["id"], "title": titolo}

    try:
        cur.execute("INSERT INTO Film (imdb_id, titolo, anno, locandina_url) VALUES (%s, %s, %s, %s) RETURNING id", (imdb_id, titolo, anno, locandina))
        movie_id = cur.fetchone()["id"]
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close(); conn.close()
    return {"status": "success", "id": movie_id, "title": titolo}

@app.put("/api/movies/{movie_id}/toggle")
def toggle_movie_watched(movie_id: int):
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE Film SET is_watched = NOT is_watched, watched_at = CASE WHEN NOT is_watched THEN %s ELSE NULL END WHERE id = %s", (datetime.now(), movie_id))
    conn.commit(); cur.close(); conn.close()
    return {"status": "success"}

@app.put("/api/movies/{movie_id}/rate")
def rate_movie(movie_id: int, req: RateRequest):
    conn = get_db(); cur = conn.cursor()
    voto = req.voto if req.voto > 0 else None
    cur.execute("UPDATE Film SET voto = %s WHERE id = %s", (voto, movie_id))
    conn.commit(); cur.close(); conn.close()
    return {"status": "success"}

@app.delete("/api/movies/{movie_id}")
def delete_movie(movie_id: int):
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM Film WHERE id = %s", (movie_id,))
    conn.commit(); cur.close(); conn.close()
    return {"status": "success"}

# ==========================================
# TV SERIES ENDPOINTS
# ==========================================
@app.get("/api/series")
def get_series():
    conn = get_db(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM Serie ORDER BY id DESC;")
    series = cur.fetchall()
    cur.close(); conn.close()
    return jsonable_encoder([dict(s) for s in series])

@app.post("/api/series/add")
def add_series(req: AddRequest):
    param = f"i={req.query}" if req.query.startswith("tt") else f"t={req.query}"
    url = f"http://www.omdbapi.com/?{param}&type=series&apikey={OMDB_API_KEY}"
    response = requests.get(url).json()
    if response.get("Response") == "False":
        raise HTTPException(status_code=404, detail="Series not found")
    
    imdb_id = response.get("imdbID")
    titolo = response.get("Title")
    year_str = response.get("Year", "").strip()
    stato = "Continuing" if year_str.endswith("-") or year_str.endswith("–") else "Ended"
    total_seasons = int(response.get("totalSeasons", 0))
    locandina = response.get("Poster")

    conn = get_db(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id FROM Serie WHERE imdb_id = %s", (imdb_id,))
    esistente = cur.fetchone()
    if esistente:
        cur.close(); conn.close()
        return {"status": "exists", "id": esistente["id"], "title": titolo}

    try:
        cur.execute("INSERT INTO Serie (imdb_id, titolo, stato, locandina_url) VALUES (%s, %s, %s, %s) RETURNING id", (imdb_id, titolo, stato, locandina))
        serie_id = cur.fetchone()["id"]
        for season in range(1, total_seasons + 1):
            s_url = f"http://www.omdbapi.com/?i={imdb_id}&Season={season}&apikey={OMDB_API_KEY}"
            s_data = requests.get(s_url).json()
            if s_data.get("Response") == "True":
                for ep in s_data.get("Episodes", []):
                    cur.execute("INSERT INTO Episodi (serie_id, stagione, numero_episodio, titolo_episodio) VALUES (%s, %s, %s, %s)", (serie_id, season, ep.get("Episode"), ep.get("Title")))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close(); conn.close()
    return {"status": "success", "id": serie_id, "title": titolo}

@app.get("/api/series/{serie_id}/episodes")
def get_episodes(serie_id: int):
    conn = get_db(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM Episodi WHERE serie_id = %s ORDER BY stagione ASC, numero_episodio ASC;", (serie_id,))
    episodes = cur.fetchall()
    cur.close(); conn.close()
    return jsonable_encoder([dict(ep) for ep in episodes])

@app.put("/api/episodes/{episode_id}/toggle")
def toggle_episode_watched(episode_id: int):
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE Episodi SET is_watched = NOT is_watched, watched_at = CASE WHEN NOT is_watched THEN %s ELSE NULL END WHERE id = %s", (datetime.now(), episode_id))
    conn.commit(); cur.close(); conn.close()
    return {"status": "success"}

@app.put("/api/episodes/{episode_id}/rate")
def rate_episode(episode_id: int, req: RateRequest):
    conn = get_db(); cur = conn.cursor()
    voto = req.voto if req.voto > 0 else None
    cur.execute("UPDATE Episodi SET voto = %s WHERE id = %s", (voto, episode_id))
    conn.commit(); cur.close(); conn.close()
    return {"status": "success"}

@app.delete("/api/series/{serie_id}")
def delete_series(serie_id: int):
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM Serie WHERE id = %s", (serie_id,))
    conn.commit(); cur.close(); conn.close()
    return {"status": "success"}

# ==========================================
# COLLECTIONS ENDPOINTS
# ==========================================
@app.get("/api/collections")
def get_collections():
    conn = get_db(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM Gruppi ORDER BY nome ASC;")
    res = cur.fetchall()
    cur.close(); conn.close()
    return jsonable_encoder([dict(r) for r in res])

@app.post("/api/collections")
def create_collection(req: CollectionRequest):
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO Gruppi (nome, tipo) VALUES (%s, %s) RETURNING id", (req.nome, req.tipo))
    c_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return {"status": "success", "id": c_id}

@app.delete("/api/collections/{c_id}")
def delete_collection(c_id: int):
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM Gruppi WHERE id = %s", (c_id,))
    conn.commit(); cur.close(); conn.close()
    return {"status": "success"}

@app.get("/api/collections/{c_id}/items")
def get_collection_items(c_id: int):
    conn = get_db(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT tipo FROM Gruppi WHERE id = %s", (c_id,))
    tipo_row = cur.fetchone()
    if not tipo_row:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Collection not found")
    tipo = tipo_row['tipo']
    
    if tipo == 'movie':
        cur.execute("""
            SELECT f.* FROM Film f 
            JOIN Gruppi_Film gf ON f.id = gf.film_id 
            WHERE gf.gruppo_id = %s ORDER BY f.titolo ASC
        """, (c_id,))
    else:
        cur.execute("""
            SELECT s.* FROM Serie s 
            JOIN Gruppi_Serie gs ON s.id = gs.serie_id 
            WHERE gs.gruppo_id = %s ORDER BY s.titolo ASC
        """, (c_id,))
    
    items = cur.fetchall()
    cur.close(); conn.close()
    return {"tipo": tipo, "items": jsonable_encoder([dict(i) for i in items])}

@app.post("/api/collections/{c_id}/sync_items")
def sync_collection_items(c_id: int, req: SyncItemsRequest):
    conn = get_db(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT tipo FROM Gruppi WHERE id = %s", (c_id,))
    tipo = cur.fetchone()['tipo']
    
    if tipo == 'movie':
        cur.execute("DELETE FROM Gruppi_Film WHERE gruppo_id = %s", (c_id,))
        for iid in req.item_ids:
            cur.execute("INSERT INTO Gruppi_Film (gruppo_id, film_id) VALUES (%s, %s)", (c_id, iid))
    else:
        cur.execute("DELETE FROM Gruppi_Serie WHERE gruppo_id = %s", (c_id,))
        for iid in req.item_ids:
            cur.execute("INSERT INTO Gruppi_Serie (gruppo_id, serie_id) VALUES (%s, %s)", (c_id, iid))
            
    conn.commit(); cur.close(); conn.close()
    return {"status": "success"}
