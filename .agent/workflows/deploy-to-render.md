---
description: Deploying a Full-Stack (React + Python) Project to GitHub and Render.com
---

To deploy a new project with a React frontend and a Python (FastAPI/Flask) backend, follow these steps:

### 1. Credentials Needed from User
Ask the user for:
1. **GitHub Personal Access Token (PAT)** with `repo` scope.
2. **GitHub Repository URL** (empty repository).
3. **Environment Variables** (contents of `.env`).

### 2. Git Initialization & Security
1. Initialize git: `git init`
2. Create a `.gitignore` at the root that excludes:
   - `node_modules/`, `dist/`, `build/`
   - `venv/`, `__pycache__/`, `.env`
   - Sensitive files like `api_keys.py`.
3. Create initial commit:
   ```bash
   git add .
   git commit -m "initial commit"
   ```

### 3. Push to GitHub
1. Rename branch to main: `git branch -M main`
2. Add remote with token:
   ```bash
   git remote add origin https://<TOKEN>@github.com/<USER>/<REPO>.git
   ```
3. Push: `git push -u origin main`
4. **Cleanup**: Remove the token from the remote URL for security:
   ```bash
   git remote set-url origin https://github.com/<USER>/<REPO>.git
   ```

### 4. Deployment Preparation (Frontend)
Ensure the React frontend uses an environment variable for its API URL:
- In `App.tsx` (or API utility), use: `const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';`
- Commit and push this change.

### 5. Render.com Setup (Manual Instructions for User)

#### Backend (Web Service)
1. **New +** -> **Web Service** -> Connect Repo.
2. **Root Directory**: `backend` (or current backend folder).
3. **Build Command**: `pip install -r requirements.txt`.
4. **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`.
5. **Environment**: Add all vars from `.env`.

#### Frontend (Static Site)
1. **New +** -> **Static Site** -> Connect Repo.
2. **Root Directory**: `frontend`.
3. **Build Command**: `npm run build`.
4. **Publish Directory**: `dist`.
5. **Environment**: Add `VITE_API_URL` pointing to the backend URL.
