# Local Demo Start

## Backend

```powershell
cd services\backend_api_v2
python -m uvicorn app.main:app --host 127.0.0.1 --port 8012
```

## Frontend

```powershell
cd services\frontend_api_v2
npm install
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open `http://127.0.0.1:5173/`.

The frontend uses relative `/api/v1` paths. The local Vite proxy forwards API requests to the local backend.
