# Campus Customs

Yale gear shop and swag stylist for MGT 409. The pages are a Vite app. The stylist is a FastAPI app. Product rows and photos stay on your machine. They are not in this repository.

## Data pack

Create this folder next to `backend/` and `frontend/`:

```
data/
├── campus_customs.db
└── products/
```

`campus_customs.db` is the catalogue, inventory, accounts, and chat tables. `products/` holds the catalogue photos. Do not commit the database or those images.

## Key

```
cp .env.example .env
```

Open `.env` and replace `replace_with_your_portkey_key` with your own Portkey key. The file name the app reads is `PORTKEY_API_KEY`.

## Back end

From this folder:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

The API is `http://127.0.0.1:8000`.

## Front end

In a second terminal, from this folder:

```
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` and `/media` to port 8000.
