# 🚀 Deployment Guide: Step-by-Step

Follow these steps to get your **Voice Scheduling Agent** live on the internet! 

---

### Phase 1: Push to GitHub 🐙
Both Render and Vercel need your code to be on GitHub.

1. **Go to [GitHub.com](https://github.com)** and create a NEW repository (name it `scheduling-agent`).
2. **Open your terminal** in the project root (`c:\Users\Shadlia\Desktop\my projects\scheduling agent`) and run these commands:
   ```bash
   git init
   git add .
   git commit -m "initial commit: voice scheduler ready"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/scheduling-agent.git
   git push -u origin main
   ```

---

### Phase 2: Deploy the Backend (Render.com) 🐍
1. **Go to [Dashboard.render.com](https://dashboard.render.com)** and sign up (connect your GitHub).
2. Click **New +** → **Web Service**.
3. Select your `scheduling-agent` repository.
4. **Settings**:
   - **Name**: `scheduling-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Environment Variables** (Click "Advanced"):
   - `PYTHON_VERSION` = `3.11.9` (CRITICAL: Do not use 3.14)
   - `GOOGLE_CLIENT_ID` = (Your key)
   - `GOOGLE_CLIENT_SECRET` = (Your key)
   - `BACKEND_PORT` = `8000`
   - `FRONTEND_URL` = (Placeholder: `https://your-app.vercel.app` — we'll update this in 5 mins)
6. Click **Deploy Web Service**.
7. **Copy your new URL** (it looks like `https://scheduling-backend.onrender.com`).

---

### Phase 3: Deploy the Frontend (Vercel) ⚛️
1. **Go to [Vercel.com](https://vercel.com)** and sign up (connect your GitHub).
2. Click **Add New** → **Project**.
3. Select your `scheduling-agent` repository.
4. **Settings**:
   - **Root Directory**: Select the `frontend` folder.
   - **Framework Preset**: Vite (should be auto-detected).
5. **Environment Variables**:
   - `VITE_API_URL` = `https://your-backend.onrender.com/api` (Paste your Render URL here!)
   - `VITE_GOOGLE_CLIENT_ID` = (Your Google Client ID)
6. Click **Deploy**.
7. **Copy your Vercel URL** (e.g., `https://scheduling-agent-xyz.vercel.app`).

---

### Phase 4: Final Google OAuth Update 🔒
Google will block logins from your new URL until you "white-list" it.

1. **Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)**.
2. Edit your **OAuth 2.0 Client ID**.
3. **Authorized JavaScript origins**: Add your Vercel URL (e.g., `https://your-app.vercel.app`).
4. **Authorized redirect URIs**: Add `https://your-app.vercel.app` (it must match EXACTLY).
5. **Save changes**.

---

### ⚠️ IMPORTANT: Update Render!
Go back to your **Render Dashboard** → **Environment Variables** and update `FRONTEND_URL` with your final Vercel link. This allows your backend to send data safely to your frontend.

**You're done! Your AI voice agent is now live!** 🚀🛰️🤖
