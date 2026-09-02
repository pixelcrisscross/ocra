# ORCA Frontend

Polished frontend for the ORCA FastAPI backend.

## Run backend

From the backend root:

```powershell
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

## Run frontend

In a second terminal:

```powershell
cd frontend
python -m http.server 5500
```

Open `http://127.0.0.1:5500`.

The UI calls `http://127.0.0.1:8000` by default.

To point to another backend in the browser console:

```js
localStorage.setItem('orca_api_base', 'http://YOUR_HOST:8000');
location.reload();
```
