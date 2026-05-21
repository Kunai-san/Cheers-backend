from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import psycopg2
import psycopg2.extras
import os
from datetime import datetime

app = FastAPI()

# CORS - dozvoli landing stranicu da poziva ovaj API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Nakon deployanja zamijeni sa svojim domenom
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

def get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS signups (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            city TEXT NOT NULL,
            city_normalized TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

# Inicijalizuj bazu pri startu
@app.on_event("startup")
def startup():
    init_db()

# ---- MODELI ----
class SignupRequest(BaseModel):
    email: str
    city: str

class SignupResponse(BaseModel):
    success: bool
    city: str
    city_count: int
    city_rank: int        # koji si po redu u svom gradu
    total_signups: int
    message: str

# ---- ENDPOINTS ----

@app.post("/signup", response_model=SignupResponse)
def signup(data: SignupRequest):
    email = data.email.strip().lower()
    city = data.city.strip()
    city_normalized = city.lower().strip()

    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Invalid email")
    if not city or len(city) < 2:
        raise HTTPException(status_code=400, detail="Invalid city")

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        # Spremi prijavu
        cur.execute(
            "INSERT INTO signups (email, city, city_normalized) VALUES (%s, %s, %s)",
            (email, city, city_normalized)
        )
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        # Email vec postoji - vrati trenutne brojeve bez greske
        cur.execute(
            "SELECT COUNT(*) FROM signups WHERE city_normalized = %s",
            (city_normalized,)
        )
        city_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM signups")
        total = cur.fetchone()[0]
        cur.close()
        conn.close()
        return SignupResponse(
            success=True,
            city=city,
            city_count=city_count,
            city_rank=city_count,
            total_signups=total,
            message=f"Already registered! {city} has {city_count} founders."
        )

    # Broj prijava za ovaj grad
    cur.execute(
        "SELECT COUNT(*) FROM signups WHERE city_normalized = %s",
        (city_normalized,)
    )
    city_count = cur.fetchone()[0]

    # Ukupno svih prijava
    cur.execute("SELECT COUNT(*) FROM signups")
    total = cur.fetchone()[0]

    cur.close()
    conn.close()

    # Poruka ovisno o poziciji
    if city_count == 1:
        message = f"You're the FIRST founder in {city}! Share to light up the map."
    elif city_count < 50:
        message = f"#{city_count} in {city}. Share to help your city win!"
    elif city_count < 500:
        message = f"{city} is heating up! #{city_count} in the race."
    else:
        message = f"{city} is on fire! #{city_count} and counting."

    return SignupResponse(
        success=True,
        city=city,
        city_count=city_count,
        city_rank=city_count,
        total_signups=total,
        message=message
    )


@app.get("/leaderboard")
def leaderboard():
    """Top 10 gradova po broju prijava - za live leaderboard na landingu"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT city, COUNT(*) as count
        FROM signups
        GROUP BY city_normalized, city
        ORDER BY count DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM signups")
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {
        "total": total,
        "cities": [{"city": r["city"], "count": r["count"]} for r in rows]
    }


@app.get("/city/{city_name}")
def city_stats(city_name: str):
    """Broj prijava za jedan grad - za progress bar"""
    normalized = city_name.lower().strip()
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM signups WHERE city_normalized = %s",
        (normalized,)
    )
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {
        "city": city_name,
        "count": count,
        "percent": round((count / 2000) * 100, 1),
        "goal": 2000
    }


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}
