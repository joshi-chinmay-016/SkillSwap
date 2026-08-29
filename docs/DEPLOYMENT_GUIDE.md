# SkillSwap Arena — Production Deployment Guide
## Vercel (Frontend) + Render (Backend) + Supabase (PostgreSQL) + Render (Redis)

This guide documents the complete end-to-end production architecture, environment variable configurations, OAuth provider setup, and deployment workflow for SkillSwap Arena.

---

## 1. System Architecture Topology

```
┌─────────────────────────────────────────────────────────────┐
│                      End User Browser                       │
└──────────────┬───────────────────────────────▲──────────────┘
               │ HTTPS                         │ WSS (WebSockets)
               ▼                               │
┌──────────────────────────────┐ ┌─────────────┴──────────────┐
│       Vercel Frontend        │ │     Render FastAPI Backend │
│   (React + Vite SPA)         │ │ (FastAPI Python Runtime)   │
│ https://<app>.vercel.app     │ │ https://skillswap-backend- │
│                              │ │     qc37.onrender.com      │
└──────────────┬───────────────┘ └─────────────┬──────────────┘
               │                               │
               │ REST API Requests             │ Direct TCP / SSL
               └──────────────────────────────►│
                                               ├──────────────────────────────┐
                                               ▼                              ▼
                                 ┌───────────────────────────┐  ┌──────────────────────────┐
                                 │    Supabase PostgreSQL    │  │       Render Redis       │
                                 │ (Session Pooler Port 6543)│  │ (TLS rediss:// Instance) │
                                 │     State & Entities      │  │  Locks, Cache, RateLimit │
                                 └───────────────────────────┘  └──────────────────────────┘
```

---

## 2. OAuth 2.0 Flow & Callback Routing

SkillSwap Arena uses a secure **two-stage authorization code + ticket handoff architecture**:

```
1. User clicks "Google" on Vercel
   └─► Redirects to Render: https://skillswap-backend-qc37.onrender.com/auth/google

2. Render generates CSRF state in Redis and redirects to Google Consent Screen

3. Google validates and redirects back to Render:
   └─► Backend Callback: https://skillswap-backend-qc37.onrender.com/auth/google/callback

4. Render exchanges auth code for Google User Info, creates/links user in Supabase,
   generates JWT access token, stores one-time ticket in Redis (60s TTL), and redirects to:
   └─► Frontend Callback: https://<your-vercel-domain>.vercel.app/auth/callback?ticket=<token>

5. Vercel frontend AuthCallback page exchanges ticket via POST /auth/oauth/exchange:
   └─► User is authenticated and redirected to /dashboard
```

### Provider Console Configurations

#### A. Google Cloud Console (APIs & Services > Credentials > OAuth 2.0 Client IDs)
* **Authorized JavaScript Origins:**
  * `http://localhost:5173` (Local Dev)
  * `https://<your-vercel-domain>.vercel.app` (Production)
* **Authorized Redirect URIs:**
  * `http://localhost:8000/auth/google/callback` (Local Dev)
  * `https://skillswap-backend-qc37.onrender.com/auth/google/callback` (Production)

#### B. GitHub Developer Settings (Settings > Developer settings > OAuth Apps)
* **Homepage URL:**
  * `https://<your-vercel-domain>.vercel.app` (or `http://localhost:5173` for dev)
* **Authorization Callback URL:**
  * `http://localhost:8000/auth/github/callback` (Local Dev)
  * `https://skillswap-backend-qc37.onrender.com/auth/github/callback` (Production)

---

## 3. Environment Variables Reference

### A. Render (Backend Web Service) Environment Variables

Configure these in your Render Dashboard (`Dashboard > Web Service > Environment`):

| Variable Name | Production Value Example / Explanation |
|---|---|
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | `postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres?sslmode=require` |
| `REDIS_URL` | `rediss://default:<password>@<render-redis-host>:<port>` |
| `SECRET_KEY` | Strong random 32+ character string (e.g. generated via `openssl rand -hex 32`) |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
| `CORS_ORIGINS` | `https://<your-vercel-domain>.vercel.app,http://localhost:5173` *(update once Vercel URL is created)* |
| `FRONTEND_URL` | `https://<your-vercel-domain>.vercel.app` *(update once Vercel URL is created)* |
| `FRONTEND_AUTH_CALLBACK_URL` | `https://<your-vercel-domain>.vercel.app/auth/callback` *(update once Vercel URL is created)* |
| `GOOGLE_CLIENT_ID` | `<your-google-client-id>.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | `<your-google-client-secret>` |
| `GOOGLE_REDIRECT_URI` | `https://skillswap-backend-qc37.onrender.com/auth/google/callback` |
| `GITHUB_CLIENT_ID` | `<your-github-client-id>` |
| `GITHUB_CLIENT_SECRET` | `<your-github-client-secret>` |
| `GITHUB_REDIRECT_URI` | `https://skillswap-backend-qc37.onrender.com/auth/github/callback` |
| `GEMINI_API_KEY` | `<your-gemini-api-key>` |
| `GEMINI_MODEL` | `gemini-1.5-flash` |
| `EMBEDDING_PROVIDER` | `gemini` |
| `FAISS_INDEX_DIR` | `vector_store` |

---

### B. Vercel (Frontend Project) Environment Variables

Configure these in your Vercel Project Settings (`Settings > Environment Variables`):

| Variable Name | Environment | Value | Notes |
|---|---|---|---|
| `VITE_API_URL` | Production & Preview | `https://skillswap-backend-qc37.onrender.com` | Backend REST API endpoint |
| `VITE_WS_URL` | Production & Preview | `skillswap-backend-qc37.onrender.com` | **Host only** — no `https://` or `wss://` prefix |

---

## 4. Step-by-Step Vercel Deployment Guide

1. **Import Git Repository to Vercel:**
   * Go to [vercel.com/new](https://vercel.com/new).
   * Select your GitHub repository (`SkillSwap`).
2. **Configure Project Settings:**
   * **Framework Preset:** `Vite`
   * **Root Directory:** `frontend` (Click *Edit* and select `frontend`).
   * **Build Command:** `npm run build` (default).
   * **Output Directory:** `dist` (default).
   * **Install Command:** `npm install` (default).
3. **Set Environment Variables:**
   * Add `VITE_API_URL` = `https://skillswap-backend-qc37.onrender.com`
   * Add `VITE_WS_URL` = `skillswap-backend-qc37.onrender.com`
4. **Deploy:**
   * Click **Deploy**. Vercel will build and assign your domain (e.g. `https://skillswap-arena.vercel.app`).
5. **Post-Deployment Final Step (Close the Loop):**
   * Copy your assigned Vercel URL (e.g., `https://skillswap-arena.vercel.app`).
   * Go to **Render Dashboard** > Your Web Service > **Environment**.
   * Update:
     * `CORS_ORIGINS` = `https://skillswap-arena.vercel.app,http://localhost:5173`
     * `FRONTEND_URL` = `https://skillswap-arena.vercel.app`
     * `FRONTEND_AUTH_CALLBACK_URL` = `https://skillswap-arena.vercel.app/auth/callback`
   * Go to **Google Cloud Console** and **GitHub OAuth Apps** and add the Vercel domain to Authorized Origins.
