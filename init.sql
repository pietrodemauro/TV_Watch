-- Movies table (Watchlist and Watched)
CREATE TABLE Film (
    id SERIAL PRIMARY KEY,
    imdb_id VARCHAR(50) UNIQUE,
    tvdb_id BIGINT,
    titolo VARCHAR(255) NOT NULL,
    anno INT,
    is_watched BOOLEAN DEFAULT FALSE,
    watched_at TIMESTAMP,
    locandina_url TEXT,
    voto INT CHECK (voto >= 1 AND voto <= 10)
);

-- Main table for TV Series
CREATE TABLE Serie (
    id SERIAL PRIMARY KEY,
    imdb_id VARCHAR(50) UNIQUE,
    tvdb_id BIGINT UNIQUE,
    titolo VARCHAR(255) NOT NULL,
    stato VARCHAR(50),
    locandina_url TEXT
);

-- Table for individual Episodes, linked to TV Series
CREATE TABLE Episodi (
    id SERIAL PRIMARY KEY,
    serie_id INT REFERENCES Serie(id) ON DELETE CASCADE,
    tvdb_id BIGINT UNIQUE,
    stagione INT NOT NULL,
    numero_episodio INT NOT NULL,
    titolo_episodio VARCHAR(255),
    is_watched BOOLEAN DEFAULT FALSE,
    watched_at TIMESTAMP,
    voto INT CHECK (voto >= 1 AND voto <= 10)
);
