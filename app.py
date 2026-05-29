import os
import math
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Put your working TMDB Key here
TMDB_API_KEY = "1eef1496d59aa06f62e201ddce2741b4"

@app.route('/api/feed', methods=['GET'])
def get_infinite_feed():
    page = request.args.get('page', default=1, type=int)
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&sort_by=popularity.desc&page={page}"
    try:
        response = requests.get(url).json()
        movies_data = []
        for item in response.get('results', []):
            poster = item.get('poster_path')
            thumb_url = f"https://image.tmdb.org/t/p/w500{poster}" if poster else "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?q=80&w=500"
            movies_data.append({
                "id": item.get('id'),
                "title": item.get('title') or item.get('original_title') or "Untitled",
                "thumbnail": thumb_url
            })
        return jsonify({"results": movies_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_catalog():
    query = request.args.get('query', default='', type=str)
    page = request.args.get('page', default=1, type=int)
    if not query:
        return jsonify({"results": []})
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={requests.utils.quote(query)}&page={page}"
    try:
        response = requests.get(url).json()
        movies_data = []
        for item in response.get('results', []):
            if not item.get('poster_path'): continue
            movies_data.append({
                "id": item.get('id'),
                "title": item.get('title') or item.get('original_title'),
                "thumbnail": f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}"
            })
        return jsonify({"results": movies_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/movie/<int:tmdb_id>', methods=['GET'])
def resolve_movie_package(tmdb_id):
    """Compiles the 4 exact keys including the direct stream source"""
    try:
        # 1 & 2. Pull official metadata fields from TMDB
        tmdb_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={TMDB_API_KEY}"
        movie_info = requests.get(tmdb_url).json()
        
        title = movie_info.get('title') or movie_info.get('original_title')
        runtime = movie_info.get('runtime', 120) 
        thumbnail = f"https://image.tmdb.org/t/p/w780{movie_info.get('poster_path')}"
        
        # 3. Direct Streaming Trailer Endpoint
        trailer_stream = f"https://vidlink.pro/trailer/{tmdb_id}"
        
        # 4. CHRONOLOGICAL SELECTION MATH ON NATIVE STREAM
        # We request VidLink's direct API endpoint to get the raw video stream array instead of an iframe
        vidlink_api = f"https://vidlink.pro/api/movie/{tmdb_id}"
        
        # Fallback to direct stream format if VidLink's raw JSON is locked by their firewall
        master_stream = f"https://vidlink.pro/movie/{tmdb_id}"
        try:
            api_response = requests.get(vidlink_api, timeout=5).json()
            if api_response.get('stream_url'):
                master_stream = api_response.get('stream_url')
        except:
            pass # Keep baseline direct stream link if API times out

        episode_length = 5
        total_episodes = math.ceil(runtime / episode_length)
        episodes_list = []
        
        for i in range(1, total_episodes + 1):
            start_seconds = (i - 1) * episode_length * 60
            episodes_list.append({
                "name": f"Ep {i}",
                "stream_url": master_stream,
                "seek_time": start_seconds
            })
            
        return jsonify({
            "title": title,
            "thumbnail": thumbnail,
            "trailer": trailer_stream,
            "episodes": episodes_list
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
