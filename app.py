from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from urllib.parse import unquote
from datetime import timedelta
from sqlalchemy import func
import os
import json
import re
import time
import threading
import google.generativeai as genai
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError
import random
import requests
import base64 # <-- NEW

# Load environment variables
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION ---
# Check if frontend is built (Production Mode)
DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'rhymic-react', 'dist'))
if os.path.exists(DIST_DIR):
    ASSETS_DIR = os.path.join(DIST_DIR, 'assets')
else:
    ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'rhymic-react', 'public', 'assets'))

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-keep-it-safe')

# Database Config (Render provides postgres:// but SQLAlchemy needs postgresql://)
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=30) # 30 Day Session
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 # 5MB Limit for Uploads

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Configure AI
ai_model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
if os.getenv("GOOGLE_API_KEY"):
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel(ai_model_name)
else:
    print("WARNING: GOOGLE_API_KEY not found. AI features will fail.")
    model = None

db = SQLAlchemy(app, engine_options={
    "pool_pre_ping": True,
    "pool_recycle": 300,
})
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    profile_pic = db.Column(db.Text, default=None)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    artist = db.Column(db.String(100), default="Unknown Artist")
    src = db.Column(db.String(300), nullable=False, unique=True)
    cover = db.Column(db.String(300), default="/assets/default_cover.jpg")

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_system = db.Column(db.Boolean, default=False)

class PlaylistSong(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)

class LikedSong(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)

# NEW MODEL: Cache for Artist Images
class ArtistImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artist_name = db.Column(db.String(100), unique=True, nullable=False)
    image_url = db.Column(db.String(500), nullable=False)

# --- SCANNER ---
def scan_library():
    music_dir = os.path.join(ASSETS_DIR, 'music')
    if not os.path.exists(music_dir): return

    for root, dirs, files in os.walk(music_dir):
        if root == music_dir: continue
        
        rel_path = os.path.relpath(root, music_dir)
        categories = rel_path.split(os.sep)
        
        folder_cover = "/assets/default_cover.jpg"
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                rel_path_img = os.path.relpath(os.path.join(root, file), os.path.join(ASSETS_DIR, '..'))
                folder_cover = f"/{rel_path_img.replace(os.sep, '/')}"
                break

        for file in files:
            if file.lower().endswith('.mp3'):
                rel_path_file = os.path.relpath(os.path.join(root, file), os.path.join(ASSETS_DIR, '..'))
                web_src = f"/{rel_path_file.replace(os.sep, '/')}"
                
                base_name = os.path.splitext(file)[0]
                clean_title = base_name
                clean_artist = "Unknown Artist"

                if ' - ' in base_name:
                    parts = base_name.split(' - ', 1)
                    clean_artist = parts[0].strip()
                    clean_title = parts[1].strip()

                song = Song.query.filter_by(src=web_src).first()
                
                if not song:
                    web_cover = folder_cover
                    for ext in ['.jpg', '.jpeg', '.png']:
                        if os.path.exists(os.path.join(root, base_name + ext)):
                            rel_c = os.path.relpath(os.path.join(root, base_name + ext), os.path.join(ASSETS_DIR, '..'))
                            web_cover = f"/{rel_c.replace(os.sep, '/')}"
                            break
                    
                    song = Song(title=clean_title, artist=clean_artist, src=web_src, cover=web_cover)
                    db.session.add(song)
                    db.session.commit()

                for category in categories:
                    if not category: continue
                    playlist = Playlist.query.filter_by(name=category, is_system=True).first()
                    if not playlist:
                        playlist = Playlist(name=category, is_system=True, user_id=None)
                        db.session.add(playlist)
                        db.session.commit()
                    
                    link = PlaylistSong.query.filter_by(playlist_id=playlist.id, song_id=song.id).first()
                    if not link:
                        link = PlaylistSong(playlist_id=playlist.id, song_id=song.id)
                        db.session.add(link)
                        db.session.commit()

# --- UPDATED: SAFE METADATA FIXER ---
def auto_fix_metadata():
    """
    Continuously checks for songs with bad metadata and fixes them in batches.
    Runs until no more 'Unknown' songs are found.
    """
    if not model: return
    
    print("Metadata Fixer: Background thread started.")
    
    while True:
        with app.app_context():
            # Check for songs with bad metadata
            # Exclude 'Unknown (AI Checked)' to avoid infinite loops on failed files
            messy_songs = Song.query.filter(
                (Song.artist == "Unknown Artist") | (Song.artist == "Unknown")
            ).limit(10).all() 
            
            if not messy_songs:
                print("Metadata Fixer: All songs processed. Sleeping 60s before next check...")
                time.sleep(60) # Keep thread alive but sleep long
                continue

            print(f"Metadata Fixer: Processing batch of {len(messy_songs)} songs...")

            for song in messy_songs:
                filename = os.path.basename(song.src)
                
                ai_prompt = f"""
                Filename: "{filename}"
                Task: Identify 'Artist' and 'Title'.
                Rules: Use your music knowledge. Remove 'official', 'lyrics', 'mp3'.
                Return JSON ONLY: {{"artist": "Name", "title": "Title"}}
                """
                
                try:
                    response = model.generate_content(ai_prompt)
                    clean_text = response.text.replace("```json", "").replace("```", "").strip()
                    match = re.search(r'\{.*\}', clean_text, re.DOTALL)
                    
                    if match:
                        data = json.loads(match.group(0))
                        if data.get('artist') and data['artist'] != 'Unknown':
                            song.artist = data['artist']
                            song.title = data['title']
                            print(f"   -> Fixed: {song.title} by {song.artist}")
                        else:
                             song.artist = "Unknown (AI Checked)"
                    else:
                        song.artist = "Unknown (AI Checked)"
                    
                    db.session.commit()
                    time.sleep(2) # Rate limit
                    
                except Exception as e:
                    print(f"   -> Failed {filename}: {e}")
                    song.artist = "Unknown (AI Checked)" # Prevent infinite loop
                    db.session.commit()
            
            time.sleep(5) # Pause between batches

# --- HELPER: FETCH ARTIST IMAGE ---
def get_artist_image(artist_name):
    """
    Checks DB for cached image. If missing, fetches from Deezer API and saves it.
    """
    # 1. Check Cache
    cached = ArtistImage.query.filter_by(artist_name=artist_name).first()
    if cached:
        return cached.image_url
    
    # 2. Fetch from Deezer
    try:
        # Search for the artist
        response = requests.get(f'https://api.deezer.com/search/artist?q={artist_name}')
        data = response.json()
        
        if data and 'data' in data and len(data['data']) > 0:
            # Get the first result's XL picture
            image_url = data['data'][0].get('picture_xl') or data['data'][0].get('picture_medium')
            
            if image_url:
                # 3. Save to Cache
                new_entry = ArtistImage(artist_name=artist_name, image_url=image_url)
                db.session.add(new_entry)
                db.session.commit()
                return image_url
                
    except Exception as e:
        print(f"Deezer API Error: {e}")
    
    # 4. Fallback (Use local default if online fetch fails)
    return '/assets/default_cover.jpg'

# --- ROUTES ---

# --- FRONTEND SERVING ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    # DIST_DIR is defined in Configuration section
    if not os.path.exists(DIST_DIR):
        return "Rhymic Backend Running (Frontend not built)", 200

    if path != "" and os.path.exists(os.path.join(DIST_DIR, path)):
        return send_from_directory(DIST_DIR, path)
    
    # Handle SPA routing (return index.html)
    if os.path.exists(os.path.join(DIST_DIR, 'index.html')):
        return send_from_directory(DIST_DIR, 'index.html')

    return "Rhymic Frontend Error", 404

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    try: return send_from_directory(ASSETS_DIR, unquote(filename))
    except: 
        if filename.endswith(('.jpg', '.png')): return send_from_directory(ASSETS_DIR, 'default_cover.jpg')
        return "Not Found", 404

# --- AI ROUTE ---
@app.route('/api/ai/recommend', methods=['POST'])
@jwt_required()
def recommend_songs():
    # Fallback: Random songs
    def get_fallback():
        all_s = Song.query.all()
        return random.sample(all_s, min(len(all_s), 10)) if all_s else []
    
    if not model: return jsonify([{'id': s.id, 'title': s.title, 'artist': s.artist, 'src': s.src, 'cover': s.cover} for s in get_fallback()])

    data = request.get_json()
    user_prompt = data.get('prompt')
    
    all_songs = Song.query.all()
    
    # Context: Include 'path' so AI sees the folder structure (e.g., "assets/music/Hindi/Song.mp3")
    library_context = [
        {
            'id': s.id, 
            'title': s.title, 
            'artist': s.artist, 
            'path': s.src 
        } 
        for s in all_songs
    ]

    # --- STRICTER PROMPT ---
    ai_prompt = f"""
    Role: Precise Music Librarian.
    User Request: "{user_prompt}"
    
    Library Data (List of Songs with Paths):
    {json.dumps(library_context)}
    
    INSTRUCTIONS:
    1. Analyze the 'path' field carefully. It contains the Genre/Language (e.g. 'Hindi', 'English', 'Rap').
    2. IF the user explicitly asks for a Language/Genre (e.g. "Hindi", "English", "Rap"):
       - You MUST ONLY select songs where that word appears in the 'path'.
       - Do NOT include songs from other folders.
    3. IF the user asks for a Vibe (e.g. "Sad", "Party"):
       - Select songs based on Title/Artist vibes.
    4. IF the request is "Mixed":
       - Pick a variety.
       
    Output: Return ONLY a raw JSON array of Song IDs. Example: [2, 9, 14]
    """

    try:
        response = model.generate_content(ai_prompt)
        match = re.search(r'\[.*\]', response.text.replace("```json", ""), re.DOTALL)
        ids = json.loads(match.group(0)) if match else []
        
        # Fetch songs preserving AI order
        result_songs = []
        for sid in ids:
            song = Song.query.get(sid)
            if song:
                result_songs.append({
                    'id': song.id, 
                    'title': song.title, 
                    'artist': song.artist, 
                    'src': song.src, 
                    'cover': song.cover
                })
        
        if not result_songs: return jsonify([{'id': s.id, 'title': s.title, 'artist': s.artist, 'src': s.src, 'cover': s.cover} for s in get_fallback()])

        return jsonify(result_songs)
    except Exception as e:
        print(f"AI Error: {e}")
        return jsonify([{'id': s.id, 'title': s.title, 'artist': s.artist, 'src': s.src, 'cover': s.cover} for s in get_fallback()])

# --- STANDARD ROUTES ---
@app.route('/api/songs', methods=['GET'])
def get_songs():
    return jsonify([{'id': s.id, 'title': s.title, 'artist': s.artist, 'src': s.src, 'cover': s.cover} for s in Song.query.all()])

@app.route('/api/playlists', methods=['GET'])
@jwt_required()
def get_playlists():
    user_id = get_jwt_identity()
    user_p = Playlist.query.filter_by(user_id=user_id).all()
    sys_p = Playlist.query.filter_by(is_system=True).all()
    output = []
    for p in sys_p: output.append({'id': p.id, 'name': p.name, 'is_system': True})
    for p in user_p: output.append({'id': p.id, 'name': p.name, 'is_system': False})
    return jsonify(output)

@app.route('/api/playlists/<int:playlist_id>', methods=['GET'])
@jwt_required()
def get_playlist_details(playlist_id):
    user_id = get_jwt_identity()
    playlist = Playlist.query.get(playlist_id)
    if not playlist: return jsonify({"message": "Not found"}), 404
    if not playlist.is_system and str(playlist.user_id) != str(user_id): return jsonify({"message": "Access denied"}), 403
    song_ids = [ps.song_id for ps in PlaylistSong.query.filter_by(playlist_id=playlist_id).all()]
    songs = Song.query.filter(Song.id.in_(song_ids)).all()
    return jsonify({
        "id": playlist.id, "name": playlist.name, "is_system": playlist.is_system,
        "songs": [{'id': s.id, 'title': s.title, 'artist': s.artist, 'src': s.src, 'cover': s.cover} for s in songs]
    })

@app.route('/api/playlists', methods=['POST'])
@jwt_required()
def create_playlist():
    user_id = get_jwt_identity()
    new_p = Playlist(name=request.get_json().get('name'), user_id=user_id)
    db.session.add(new_p); db.session.commit()
    return jsonify({'id': new_p.id, 'name': new_p.name}), 201

@app.route('/api/playlists/add_song', methods=['POST'])
@jwt_required()
def add_song():
    user_id = get_jwt_identity()
    data = request.get_json()
    pid, sid = data.get('playlist_id'), data.get('song_id')
    if not Playlist.query.filter_by(id=pid, user_id=user_id).first(): return jsonify({"message": "Error"}), 404
    if not PlaylistSong.query.filter_by(playlist_id=pid, song_id=sid).first():
        db.session.add(PlaylistSong(playlist_id=pid, song_id=sid)); db.session.commit()
    return jsonify({"message": "Added"}), 200

@app.route('/api/likes', methods=['GET'])
@jwt_required()
def get_likes():
    return jsonify([l.song_id for l in LikedSong.query.filter_by(user_id=get_jwt_identity()).all()])

@app.route('/api/likes', methods=['POST'])
@jwt_required()
def toggle_like():
    user_id = get_jwt_identity(); sid = request.get_json().get('song_id')
    existing = LikedSong.query.filter_by(user_id=user_id, song_id=sid).first()
    if existing: db.session.delete(existing); db.session.commit(); return jsonify({"status": "removed"})
    db.session.add(LikedSong(user_id=user_id, song_id=sid)); db.session.commit(); return jsonify({"status": "added"})

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    # Pre-check (Fast)
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email already registered"}), 400
        
    hashed = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(name=data['name'], email=data['email'], password=hashed)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User created successfully"}), 201
    except IntegrityError:
        db.session.rollback() # Undo the stuck transaction
        return jsonify({"message": "Email already registered"}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Signup Error: {e}")
        return jsonify({"message": "Error creating account"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        token = create_access_token(identity=str(user.id))
        return jsonify({"token": token, "user": {"id": user.id, "name": user.name}}), 200
    return jsonify({"message": "Invalid"}), 401

# --- USER ROUTES ---
@app.route('/api/user/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user: return jsonify({"message": "User not found"}), 404
    
    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "profile_pic": user.profile_pic or None # Return null if not set
    })

@app.route('/api/user/upload_profile_pic', methods=['POST'])
@jwt_required()
def upload_profile_pic():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user: return jsonify({"message": "User not found"}), 404

    if 'image' not in request.files:
        return jsonify({"message": "No file part"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    if file:
        try:
            # Read bytes and convert to Base64
            file_data = file.read()
            b64_str = base64.b64encode(file_data).decode('utf-8')
            
            # Create Data URI
            mime_type = file.content_type or "image/jpeg"
            data_uri = f"data:{mime_type};base64,{b64_str}"

            # Update DB (Persistent Storage)
            user.profile_pic = data_uri
            db.session.commit()

            return jsonify({"message": "Uploaded successfully", "profile_pic": data_uri})
        except Exception as e:
             print(f"Upload Error: {e}")
             return jsonify({"message": "Upload failed"}), 500

# --- RUNNER ---

# Initialize App Logic (Runs on Import/Gunicorn Start)
def initialize_app():
    with app.app_context():
        try:
            db.create_all()
            
            # MIGRATION: Attempt to add/update profile_pic column safely
            try:
                with db.engine.connect() as conn:
                    from sqlalchemy import text
                    # 1. Try adding if missing
                    try:
                        conn.execute(text("ALTER TABLE user ADD COLUMN profile_pic TEXT"))
                        conn.commit()
                        print("Migrated: Added profile_pic column")
                    except Exception:
                        # 2. If exists, ensure it is TEXT (for Base64 support)
                        conn.execute(text("ALTER TABLE user ALTER COLUMN profile_pic TYPE TEXT"))
                        conn.commit()
                        print("Migrated: Updated profile_pic to TEXT")
            except Exception as e:
                print(f"Migration Note: {e}")
            
            # Scan Library (Fast)
            scan_library()

            # Background Metadata Fixer (Slow)
            if model:
                def run_background_fix():
                    with app.app_context():
                        auto_fix_metadata()
                
                thread = threading.Thread(target=run_background_fix)
                thread.daemon = True
                thread.start()
                
        except Exception as e:
            print(f"Initialization Error: {e}")

# Run initialization
initialize_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)