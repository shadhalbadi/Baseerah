# Baseerah — Frontend (Vite + React + TS)

Bilingual (Arabic/English, RTL-aware) SPA for the Baseerah utility-intelligence API.

## Stack
- **Vite + React 19 + TypeScript**
- **Tailwind CSS v4** (`@tailwindcss/vite`)
- **react-router-dom** (routing) · **react-i18next** (AR/EN + RTL)
- Auth via JWT bearer token in `localStorage`

## Setup

```bash
cd frontend
npm install
cp .env.example .env   # optional; defaults to http://127.0.0.1:8000
```

## Run

The backend must be running first (see `../backend/README.md`).

```bash
npm run dev      # http://localhost:5173
```

`npm run build` type-checks (`tsc -b`) and builds for production.

## Config
- `VITE_API_URL` — backend base URL (default `http://127.0.0.1:8000`).
- The backend must allow the frontend origin via CORS (`BASEERAH_CORS_ORIGINS`).

## Flow
Register → auto-login → **Properties** → open a property → add bills → **Analyze**
(baseline, anomaly status, leak/fault, forecast, ranked recommendations).
Toggle AR/EN from the header; the layout flips to RTL for Arabic.

## Layout

```
src/
  main.tsx              # entry: mounts App, loads i18n
  App.tsx               # router + AuthProvider
  config.ts             # API_URL, token key
  types.ts              # API DTOs (mirror backend schemas)
  i18n.ts               # i18next init + dynamic html dir/lang
  locales/{en,ar}.json  # translations
  api/client.ts         # typed fetch wrapper (bearer token, ApiError)
  auth/AuthContext.tsx  # login/register/logout, session bootstrap
  components/           # Layout, ProtectedRoute, LanguageSwitcher, AnalysisView, ui
  pages/                # Login, Register, Properties, PropertyDetail
```
