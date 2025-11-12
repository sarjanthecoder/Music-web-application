from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import requests
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Logging setup
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Fetch YouTube API Key from environment
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not YOUTUBE_API_KEY:
    logger.warning("⚠️ YOUTUBE_API_KEY not found in environment variables. Please check your .env file.")

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '').strip()
    logger.info(f"🔍 Searching for: {query}")

    if not query:
        return jsonify({"error": "No search query provided"}), 400

    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'type': 'video',
            'q': f'{query} music',
            'maxResults': 12,
            'key': YOUTUBE_API_KEY,
            'order': 'relevance'
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'error' in data:
            error_msg = data['error'].get('message', 'Unknown error')
            logger.error(f"❌ YouTube API error: {error_msg}")
            return jsonify({"error": f"API Error: {error_msg}"}), 400

        results = []
        for item in data.get("items", []):
            try:
                results.append({
                    "title": item["snippet"]["title"],
                    "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                    "videoId": item["id"]["videoId"],
                    "channel": item["snippet"]["channelTitle"],
                })
            except KeyError:
                continue

        logger.info(f"✅ Found {len(results)} videos for query '{query}'")
        return jsonify(results)

    except Exception as e:
        logger.exception("Error during YouTube search")
        return jsonify({"error": str(e)}), 500


@app.route('/get-audio/<video_id>', methods=['GET'])
def get_audio(video_id):
    logger.info(f"🎧 Fetching audio for video ID: {video_id}")

    try:
        from yt_dlp import YoutubeDL
    except ImportError:
        logger.error("❌ yt-dlp not installed. Run: pip install yt-dlp")
        return jsonify({"error": "yt-dlp not installed"}), 500

    try:
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/mp3/bestaudio',
            'quiet': True,
            'no_warnings': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
            audio_url = info.get('url')
            if not audio_url:
                raise Exception("No audio URL found in video info")

        logger.info(f"✅ Got audio URL: {audio_url[:80]}...")

        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(audio_url, stream=True, timeout=120, headers=headers, allow_redirects=True)
        response.raise_for_status()

        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        return Response(
            generate(),
            mimetype='audio/mp4',
            headers={
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'audio/mp4',
                'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0',
                'Connection': 'keep-alive'
            }
        )

    except Exception as e:
        logger.exception(f"❌ Streaming failed for {video_id}")
        return jsonify({"error": str(e)}), 500
