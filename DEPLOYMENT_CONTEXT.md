# Rhymic Deployment Planning Context

## Current State
**Project:** Self-Hosted Music Streaming App (Python Flask + React Vite).
**Database:** SQLite (`instance/site.db`).
**File Storage:** Local filesystem (`rhymic-react/public/assets/` for music and user uploads).
**Authentication:** Flask-JWT-Extended (Stateless).
**AI:** Google Gemini API (Key required).

## Deployment Goal
Deploy to a cloud provider (likely **Render.com** or **Railway.app**) to make the app accessible publicly.

## Critical Constraints & Architecture Analysis
The current architecture relies on a **persistent local filesystem**, which poses major issues for cloud deployment:

1.  **Database (SQLite):** 
    - *Current:* Stored in a local file.
    - *Problem:* Cloud containers are ephemeral. The database will wipe on every deploy/restart.
    - *Requirement:* Migrate to **PostgreSQL**.

2.  **User Uploads (Profile Pics):**
    - *Current:* Saved to `rhymic-react/public/assets/users`.
    - *Problem:* These files will disappear on restart.
    - *Requirement:* Migrate to **Cloudinary** (easiest for images) or **AWS S3**.

3.  **Music Library:**
    - *Current:* Scanned from local folder `public/assets/music`.
    - *Constraint:* If the user wants to *add* music dynamically, we need S3. If the library is static (committed to Git), the current method works but increases repo size.
    - *Decision Point:* Assume static library for MVP, or migrate to S3 for a true "streaming service" feel.

4.  **Frontend/Backend Serving:**
    - *Current:* Two separate terminals (`npm run dev` and `python app.py`).
    - *Requirement:* 
        - **Option A (Unified):** Build React (`npm run build`) and have Flask serve the static `dist/` folder. (Cheaper, single service).
        - **Option B (Decoupled):** Deploy React to Vercel/Netlify and Flask to Render. (Easier scaling, CORS configuration needed).

## Task List for Gemini
1.  **Refactor Database:** Update `app.py` to use `os.environ.get('DATABASE_URL')` and switch to Postgres in production.
2.  **Refactor Storage:** Implement a cloud storage adapter (e.g., using `cloudinary` python package) for profile pictures.
3.  **Production Build:** Create a `build.sh` script to install Python deps, install Node deps, build React, and move assets.
4.  **WSGI Server:** Ensure `gunicorn` is configured correctly (`Procfile`).
5.  **Environment Variables:** List all required secrets (`GOOGLE_API_KEY`, `SECRET_KEY`, `DATABASE_URL`, `CLOUDINARY_URL`).
