# Cheers Backend

FastAPI backend za Cheers waitlist — prima prijave, broji po gradu, vraća live statistiku.

## Endpoints

| Metoda | URL | Opis |
|--------|-----|------|
| POST | `/signup` | Prima email + city, vraca broj prijava za taj grad |
| GET | `/leaderboard` | Top 10 gradova za live leaderboard |
| GET | `/city/{city_name}` | Stats za jedan grad (progress bar) |
| GET | `/health` | Health check |

---

## Deployment na Railway (korak po korak)

### 1. Upload na GitHub
- Idi na github.com → "Create repository"
- Naziv: `cheers-backend`
- Public ili Private (svejedno)
- Klikni "Create repository"
- Upload fajlove: `main.py`, `requirements.txt`, `Procfile`

### 2. Railway setup
- Idi na railway.app → "Login with GitHub"
- "New Project" → "Deploy from GitHub repo"
- Izaberi `cheers-backend`
- Railway automatski detektuje Python i instalira sve

### 3. Dodaj PostgreSQL bazu
- U Railway projektu: "New" → "Database" → "PostgreSQL"
- Railway automatski postavi `DATABASE_URL` environment varijablu
- Backend je odmah spreman

### 4. Dobij svoj URL
- U Railway: Settings → Domains → "Generate Domain"
- Dobijes nesto kao: `cheers-backend-production.up.railway.app`
- Taj URL koristis u landing stranici

### 5. Povezi landing stranicu
U `cheers-landing.html` promijeni:
```javascript
const API_URL = "https://TVOJ-URL.up.railway.app";
```

---

## Testiranje

Nakon deployanja, otvori browser i idi na:
```
https://TVOJ-URL.up.railway.app/health
```
Trebas vidjeti: `{"status": "ok", ...}`

Testiranje signup-a:
```
https://TVOJ-URL.up.railway.app/docs
```
Railway automatski generise Swagger UI gdje mozes testirati sve endpointe.

---

## Troskovi

- Railway: besplatno do $5/mj prometa (vise nego dovoljno za prvih 10.000 prijava)
- PostgreSQL: besplatno u Railway
- Ukupno: $0 dok ne prodes 50.000 zahtjeva/mj
