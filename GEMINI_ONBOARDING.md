# Rhymic Project Context (Master Onboarding)

**Project Name:** Rhymic AI-Powered Music Streaming App
**Type:** Self-Hosted Web Application
**Current Date:** January 13, 2026

## 1. High-Level Architecture
Rhymic is a full-stack music streaming app consisting of a **Python Flask backend** and a **React (Vite) frontend**.
- **Backend:** Serves the REST API, manages the SQLite database, handles authentication (JWT), and serves static music files/images.
- **Frontend:** A Single Page Application (SPA) consuming the API, managing playback state via Zustand, and handling UI/UX.

## 2. Tech Stack
- **Backend:** Python 3.11+, Flask, SQLAlchemy (ORM), Flask-JWT-Extended, Google Generative AI (Gemini).
- **Frontend:** React 19, Vite, Zustand (State), React Router DOM v7, CSS Modules (standard CSS).
- **Database:** SQLite (`instance/site.db`).
- **Styling:** CSS Modules with global variables for theming (Light/Dark modes).

## 3. Key Backend Logic (`app.py`)
- **Library Scanning (`scan_library`):** 
    - Recursively scans `rhymic-react/public/assets/music`.
    - Automatically creates `Song`, `Album` (implicit), and `Playlist` (based on folder names) entries.
    - Prevents duplicates using file paths as unique keys.
- **AI Integration (`auto_fix_metadata` & `recommend_songs`):**
    - Uses `google.generativeai` to fix "Unknown Artist" metadata by analyzing filenames.
    - **Smart DJ:** Accepts natural language prompts (e.g., "Sad songs from the 90s") to generate playlists using context-aware AI.
- **User System:**
    - `User` model includes `profile_pic` (path string).
    - Custom route `/api/user/upload_profile_pic` saves images to `assets/users` and updates the DB.
    - JWT tokens valid for 30 days.

## 4. Key Frontend Logic
- **Store (`musicStore.js`):**
    - **`songs`**: Acts as the current context/queue.
    - **`addToQueue` / `playNext`**: Custom actions to manipulate the `songs` array for queuing.
    - **`currentSong`**: The active track object.
- **Audio Engine (`useAudio.js`):**
    - Custom hook wrapping `new Audio()`.
    - Handles play/pause syncing with store state.
    - **Limitation:** No crossfade/gapless (standard HTML5 Audio).
- **Routing (`App.jsx`):**
    - **Protected Routes:** Checks `authStore.token`. If missing, renders *only* Login/Signup routes.
    - **Redirects:** Unauthenticated users hitting `/` go to `/login`. Authenticated users hitting `/login` go to `/`.

## 5. Recent Customizations & Features
- **Context Menu:** Right-click on songs in `PlaylistDetails` to "Play Next" or "Add to Queue".
- **Profile Picture:** Users can upload avatars. Images are stored locally and served statically. Max size 5MB.
- **UI "Mood" Matching:**
    - The Footer (ProgressBar), Volume Slider, and Queue Popup use `background-attachment: fixed` with `var(--bg-primary)` and `var(--bg-gradient)` to seamlessly blend with the homepage background while remaining solid (non-transparent).
    - Queue Popup uses a dedicated CSS module `QueuePopup.module.css` to fix z-index overlapping.

## 6. Directory Structure Overview
```
/
├── app.py                  # Main Flask Server
├── instance/site.db        # SQLite Database
└── rhymic-react/           # Frontend Root
    ├── src/
    │   ├── components/     # UI Components (Sidebar, Topbar, Player, QueuePopup)
    │   ├── store/          # Zustand Stores (musicStore, authStore)
    │   ├── pages/          # Full pages (ComingSoon)
    │   └── App.jsx         # Main Router & Layout Logic
    └── public/assets/      # Stores Music and User Uploads
```

## 7. How to Run
1. **Backend:** `python app.py` (Runs on port 5000)
2. **Frontend:** `npm run dev` (Runs on port 5173, proxies /api to localhost:5000)
