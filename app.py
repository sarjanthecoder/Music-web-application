from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import requests
import logging
import subprocess
import os
import tempfile

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

YOUTUBE_API_KEY = "AIzaSyCWtllysGRv3D8eQPR5_xcIwRUDsSKd-V4"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '').strip()
    logger.info(f"🔍 Search: {query}")
    
    if not query:
        return jsonify({"error": "No search query"}), 400

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
                result = {
                    "title": item["snippet"]["title"],
                    "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                    "videoId": item["id"]["videoId"],
                    "channel": item["snippet"]["channelTitle"],
                }
                results.append(result)
                logger.info(f"✅ {result['title']}")
            except KeyError:
                continue
        
        logger.info(f"Found {len(results)} songs")
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get-audio/<video_id>', methods=['GET'])
def get_audio(video_id):
    """Stream MP3 audio through our proxy to avoid CORS issues"""
    try:
        logger.info(f"🎵 Streaming audio for: {video_id}")
        
        # Use yt-dlp to get the best audio stream
        try:
            from yt_dlp import YoutubeDL
            
            ydl_opts = {
                'format': 'bestaudio',
                'quiet': True,
                'no_warnings': True,
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
                audio_url = info.get('url')
                
                if not audio_url:
                    raise Exception("No audio URL found")
                
                logger.info(f"✅ Got audio stream, proxying...")
                
                # Stream the audio through our server to bypass CORS
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(audio_url, stream=True, timeout=30, headers=headers)
                response.raise_for_status()
                
                def generate():
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk
                
                return Response(
                    generate(),
                    mimetype='audio/mpeg',
                    headers={
                        'Content-Type': 'audio/mpeg',
                        'Access-Control-Allow-Origin': '*',
                        'Content-Length': response.headers.get('Content-Length'),
                    }
                )
        
        except ImportError:
            logger.error("❌ yt-dlp not installed")
            return jsonify({"error": "yt-dlp not installed. Run: pip install yt-dlp"}), 500
            
    except Exception as e:
        logger.error(f"❌ Streaming error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    logger.info("🚀 Starting Songify...")
    app.run(debug=True, host='127.0.0.1', port=5000)