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
`docker-compose up -d`

Once running, open Adminer (port 8085 by default), log into your PostgreSQL database, and execute the SQL script found in init.sql to generate the tables.

### 3. Setup the Backend

Clone the repository on your server and create a virtual environment:
`
sudo apt update
sudo apt install python3-pip python3-venv
mkdir tvtracker_backend && cd tvtracker_backend`

# Create and activate virtual environment
`python3 -m venv venv
source venv/bin/activate`

# Install requirements
`pip install fastapi uvicorn psycopg2-binary requests pydantic`

Edit main.py and sync_episodes.py to add your OMDB API Key and your PostgreSQL credentials.
### 4. Run the Server

Ensure index.html is in the same directory as main.py. Test the server:

`uvicorn main:app --host 0.0.0.0 --port 8010`

Navigate to http://YOUR_SERVER_IP:8010 from any device on your local network to access the web app.
### 5. Run as a Systemd Service (Production)

To keep the API running permanently in the background, create a systemd service:

`sudo nano /etc/systemd/system/tvtracker-api.service`

Insert the following (replace YOUR_USERNAME):
```
Ini, TOML

[Unit]
Description=TV Tracker FastAPI Backend
After=network.target 

[Service]
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/tvtracker_backend
ExecStart=/home/YOUR_USERNAME/tvtracker_backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8010
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

`sudo systemctl daemon-reload
sudo systemctl enable tvtracker-api
sudo systemctl start tvtracker-api`

### 6. Setup the Background Cron Job

To automatically sync new episodes for your continuing series, set up a cron job:

`crontab -e`

Add the following line to run the sync every day at 3:00 AM (replace YOUR_USERNAME):
Bash

`0 3 * * * /home/YOUR_USERNAME/tvtracker_backend/venv/bin/python /home/YOUR_USERNAME/tvtracker_backend/sync_episodes.py >> /home/YOUR_USERNAME/tvtracker_backend/sync_cron.log 2>&1`

### 🔄 Optional: Migrate from TV Time
If you are moving away from the TV Time app, you can easily import all your watch history (movies and TV shows) into your new local database.

To get your data:
1. Install the **"TV TIME OUT BY REFRACT"** extension in your web browser.
2. Log in to your account on the official TV Time website.
3. Use the extension to generate and download the JSON export of your profile.
4. Place the downloaded files in the same folder as this project and rename them to `tvtime-movies.json` and `tvtime-series.json`.

Once the files are in place, simply run the provided migration script:
`python import_tvtime.py`

### 📝 License

This project is open-source and available under the GPL-3.0 license.
