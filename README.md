# 📺 TV Tracker Pro

A self-hosted, lightweight, and blazing fast web application to track the movies and TV shows you watch. Built with **FastAPI**, **PostgreSQL**, and a modern **Vanilla JS + TailwindCSS** frontend.

It seamlessly integrates with the **OMDB API** to automatically fetch metadata, posters, and new episodes for continuing series in the background.

## 🚀 Features

* **Movies & Watchlist:** Add movies by Title or IMDB ID. Move them seamlessly between your Watchlist and Watched list.
* **Smart TV Shows Tracking:** Add a TV Show and the backend will automatically map all its seasons and episodes. 
* **Background Sync:** Includes a Python Cron job that checks for new episodes of continuing series while you sleep.
* **Rating System:** Rate your movies and individual episodes from 1 to 10.
* **Single Page Application:** Fluid UX. The interface auto-scrolls to items if you try to add an existing movie or show.
* **Docker Ready:** Designed to be easily spun up on environments like CasaOS or standard Ubuntu servers.

## 🛠 Tech Stack

* **Backend:** Python 3, FastAPI, Psycopg2, Uvicorn
* **Database:** PostgreSQL (Containerized) + Adminer
* **Frontend:** HTML5, Vanilla JavaScript, TailwindCSS (CDN)
* **API:** OMDB API

## 📦 Installation Guide (Ubuntu / CasaOS)

### 1. Prerequisites
You need an API key from OMDB. You can get a free one (1000 requests/day) at [omdbapi.com](http://www.omdbapi.com).

### 2. Setup the Database
Use the provided `docker-compose.yml` to spin up PostgreSQL and Adminer.
```bash
docker-compose up -d
