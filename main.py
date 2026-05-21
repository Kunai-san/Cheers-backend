from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncpg
import os
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

async def get_db():
    return await asyncpg.connect(os.environ["DATABASE_URL"])

@app.on_event("startup")
async def startup():
    conn = await get_db()
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS signups (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            city TEXT NOT NULL,
            city_normalized TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    await conn.close()

class SignupRequest(BaseModel):
    email: str
    city: str

@app.post("/signup")
async def signup(data: SignupRequest):
    email = data.email.strip().lower()
    city = data.city.strip()
    city_normalized = city.lower().strip()

    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Invalid email")
    if not city or len(city) < 2:
        raise HTTPException(status_code=400, detail="Invalid city")

    conn = await get_db()
    try:
        try:
            await conn.execute(
                "INSERT INTO signups (email, city, city_normalized) VALUES ($1, $2, $3)",
                email, city, city_normalized
            )
        except asyncpg.UniqueViolationError:
            pass  # Email vec postoji, nastavljamo

        city_count = await conn.fetchval(
            "SELECT COUNT(*) FROM signups WHERE city_normalized = $1", city_normalized
        )
        total = await conn.fetchval("SELECT COUNT(*) FROM signups")

    finally:
        await conn.close()

    if city_count == 1:
        message = f"You're the FIRST founder in {city}! Share to light up the map."
    elif city_count < 50:
        message = f"#{city_count} in {city}. Share to help your city win!"
    elif city_count < 500:
        message = f"{city} is heating up! #{city_count} in the race."
    else:
        message = f"{city} is on fire! #{city_count} and counting."

    return {
        "success": True,
        "city": city,
        "city_count": int(city_count),
        "city_rank": int(city_count),
        "total_signups": int(total),
        "message": message
    }

@app.get("/leaderboard")
async def leaderboard():
    conn = await get_db()
    try:
        rows = await conn.fetch("""
            SELECT city, COUNT(*) as count
            FROM signups
            GROUP BY city_normalized, city
            ORDER BY count DESC
            LIMIT 10
        """)
        total = await conn.fetchval("SELECT COUNT(*) FROM signups")
    finally:
        await conn.close()

    return {
        "total": int(total),
        "cities": [{"city": r["city"], "count": int(r["count"])} for r in rows]
    }

@app.get("/city/{city_name}")
async def city_stats(city_name: str):
    normalized = city_name.lower().strip()
    conn = await get_db()
    try:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM signups WHERE city_normalized = $1", normalized
        )
    finally:
        await conn.close()
    return {
        "city": city_name,
        "count": int(count),
        "percent": round((int(count) / 2000) * 100, 1),
        "goal": 2000
    }

@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now().isoformat()}
 
