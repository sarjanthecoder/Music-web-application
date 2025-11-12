from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import requests
import logging
import os
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# ✅ Logging setup
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ✅ YouTube API key from .env
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not YOUTUBE_API_KEY:
    logger.warning("⚠️ YOUTUBE_API_KEY not found! Please check your .env file.")

# -----------------------------------------------------
# 🏠 Home Route
# -----------------------------------------------------
@app.route('/')
def home():
    return render_template('index.html')


# -----------------------------------------------------
# 🔍 YouTube Search Route
# -----------------------------------------------------
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
        logger.exception("❌ Error during YouTube search")
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------
# 🎵 Stream YouTube Audio
# -----------------------------------------------------
@app.route('/get-audio/<video_id>', methods=['GET'])
def get_audio(video_id):
    """Proxy YouTube audio stream through our server to bypass CORS."""
    logger.info(f"🎧 Fetching audio for video ID: {video_id}")

    try:
        from yt_dlp import YoutubeDL
    except ImportError:
        logger.error("❌ yt-dlp not installed. Run: pip install yt-dlp")
        return jsonify({"error": "yt-dlp not installed. Run: pip install yt-dlp"}), 500

    try:
        # Fetch the best available audio stream
        ydl_opts = {'format': 'bestaudio', 'quiet': True, 'no_warnings': True}

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
            audio_url = info.get('url')

            if not audio_url:
                raise Exception("No audio stream found")

        logger.info("✅ Audio stream URL obtained successfully")

        # Stream audio through Flask proxy
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(audio_url, stream=True, timeout=60, headers=headers, allow_redirects=True)
        response.raise_for_status()

        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        return Response(
            generate(),
            mimetype='audio/mpeg',
            headers={
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'audio/mpeg',
                'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0',
                'Connection': 'keep-alive'
            }
        )

    except Exception as e:
        logger.exception(f"❌ Streaming failed for video {video_id}")
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------
# 🩺 Health Check
# -----------------------------------------------------
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


# -----------------------------------------------------
# 🚀 Run Server
# -----------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Starting Songify YouTube App on port {port}")
    app.run(host="0.0.0.0", port=port)
