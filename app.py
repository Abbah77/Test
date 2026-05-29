import os
import math
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Allow cross-origin requests from any client domain (like local testing or Vercel)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Global Read-Only Key for movie metadata extraction
TMDB_API_KEY = "c18e77519198aa7f6c31bf0d9aa1787d" 

@app.route('/api/feed', methods=['GET'])
def get_infinite_feed():
    """Generates a dynamic scroll page list of trending films straight from TMDB"""
    page = request.args.get('page', default=1, type=int)
    # Updated to an alternative high-velocity discovery route to ensure absolute data delivery
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&sort_by=popularity.desc&page={page}"
    
    try:
        response = requests.get(url).json()
        movies_data = []
        
        for item in response.get('results', []):
            # Fallback pathing logic: ensure the card populates even if a poster asset is missing
            poster = item.get('poster_path')
            thumb_url = f"https://image.tmdb.org/t/p/w500{poster}" if poster else "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?q=80&w=500"
            
            movies_data.append({
                "id": item.get('id'),
                "title": item.get('title') or item.get('original_title') or "Untitled Broadcast",
                "thumbnail": thumb_url
            })
        return jsonify({"results": movies_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_catalog():
    """Searches the worldwide TMDB database dynamically based on typing query"""
    query = request.args.get('query', default='', type=str)
    page = request.args.get('page', default=1, type=int)
    
    if not query:
        return jsonify({"results": []})
        
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={requests.utils.quote(query)}&page={page}"
    try:
        response = requests.get(url).json()
        movies_data = []
        for item in response.get('results', []):
            if not item.get('poster_path'):
                continue
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
    """Compiles the 4 exact keys expected by your frontend layout"""
    try:
        # 1 & 2. Get Title and Runtime from TMDB
        tmdb_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={TMDB_API_KEY}"
        movie_info = requests.get(tmdb_url).json()
        
        if "status_code" in movie_info and movie_info["status_code"] == 34:
            return jsonify({"error": "Movie target not found in global register"}), 404
            
        title = movie_info.get('title') or movie_info.get('original_title')
        runtime = movie_info.get('runtime', 120)  # Default fallback if runtime field is blank
        thumbnail = f"https://image.tmdb.org/t/p/w780{movie_info.get('poster_path')}"
        
        # 3. Direct Streaming Trailer Link Vector
        trailer_stream = f"https://vidlink.pro/trailer/{tmdb_id}"
        
        # 4. CHRONOLOGICAL SELECTION MATH (5-Minute Slices)
        master_stream = f"https://vidlink.pro/movie/{tmdb_id}" 
        
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
            
        # Return package back to client frontend
        return jsonify({
            "title": title,
            "thumbnail": thumbnail,
            "trailer": trailer_stream,
            "episodes": episodes_list
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Render binds the application dynamically via environment port vectors
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

