🎧 Songify - Music Streaming Backend

This is the Flask backend for Songify, a music streaming application that uses YouTube as its audio source.

The application searches YouTube for music videos, then uses yt-dlp to fetch the direct audio stream and proxy it to the frontend. This allows for playback without requiring the user to download the video and bypasses browser CORS issues.

✨ Features

YouTube Search: Search for songs, artists, or albums via the YouTube v3 API.

Audio Streaming: Efficiently streams the best available audio from a YouTube video ID.

CORS Enabled: Configured with Flask-CORS to allow requests from your frontend.

Proxy Server: Acts as a proxy to stream audio directly, preventing frontend CORS errors.

Health Check: Includes a /health endpoint for monitoring.

architecture

Here's a simple breakdown of how it works:

Frontend (index.html): The user interacts with your index.html page.

Search (POST /search):

User types a song name (e.g., "Imagine Dragons").

Frontend sends this query to the Flask backend's /search endpoint.

Flask backend uses the YouTube v3 API to find a list of matching videos.

Backend returns a JSON list of songs (title, thumbnail, videoId) to the frontend.

Play (GET /get-audio/<video_id>):

User clicks "Play" on a song.

Frontend calls the Flask backend's /get-audio/videoId_... endpoint.

Flask backend uses the yt-dlp library to get the direct URL of the audio stream from YouTube.

The Flask server streams this audio data back to the frontend, which plays it in the <audio> tag.

⚙️ Setup and Installation

Follow these steps to run the server locally.

1. Prerequisites

Python 3.8+

pip (Python package installer)

2. Clone the Repository

(If you have this in a project, you can skip this step)

git clone <your-repo-url>
cd <your-project-directory>


3. Create a Virtual Environment

It's highly recommended to use a virtual environment to manage dependencies.

On macOS/Linux:

python3 -m venv venv
source venv/bin/activate


On Windows:

python -m venv venv
.\venv\Scripts\activate


4. Install Dependencies

Install all the required Python libraries from the requirements.txt file.

pip install -r requirements.txt


🔑 Configuration

This project requires a YouTube v3 API key to search for songs.

Get your API Key:

Go to the Google Cloud Console.

Create a new project.

Enable the "YouTube Data API v3" service.

Create credentials for an "API Key".

Set your API Key:

Rename the .env.example file to .env:

mv .env.example .env


Open the new .env file and paste your API key into it:

YOUTUBE_API_KEY=AIzaSy...your...key...here...


The app.py file is configured to read this key safely without exposing it in the code.

🚀 Running the Application

Once you have installed the dependencies and configured your .env file, you can start the server:

python app.py


The server will start on http://127.0.0.1:5000.

<caption> API Endpoints

The server provides the following endpoints:

Method

Endpoint

Description

GET

/

Serves the main index.html frontend.

POST

/search

Form Data: query=<search_term>



Searches YouTube for videos matching the query and returns a JSON list of results.

GET

/get-audio/<video_id>

Streams the audio from the specified YouTube video_id as audio/mpeg.

GET

/health

A simple health check endpoint. Returns {"status": "ok"}.
