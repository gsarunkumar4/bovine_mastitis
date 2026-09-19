from fastapi import APIRouter, HTTPException
from app.services.database import connect

router = APIRouter()


@router.post("/cows")
def create_cow(cow: dict):
    if "cow_id" not in cow or "parity" not in cow:
        raise HTTPException(400, "cow_id and parity are required")
    if cow["parity"] < 1:
        raise HTTPException(400, "parity must be >= 1")
    c = connect()
    try:
        c.execute(
            """INSERT INTO cows(
                cow_id, breed, age_years, parity, calving_date,
                vaccination_status, prior_mastitis_flag, herd_id,
                latitude, longitude, location_label
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (
                cow["cow_id"],
                cow.get("breed"),
                cow.get("age_years"),
                cow["parity"],
                cow.get("calving_date"),
                cow.get("vaccination_status", 1),
                cow.get("prior_mastitis_flag", 0),
                cow.get("herd_id", "demo_herd_01"),
                cow.get("latitude"),
                cow.get("longitude"),
                cow.get("location_label"),
            ),
        )
        c.commit()
        return {"status": "created", "cow_id": cow["cow_id"]}
    finally:
        c.close()


@router.get("/cows")
def list_cows():
    c = connect()
    try:
        return [dict(r) for r in c.execute("SELECT * FROM cows ORDER BY cow_id").fetchall()]
    finally:
        c.close()


@router.get("/cows/locations")
def cow_locations():
    """§10 — Return all cows with their coordinates for map rendering."""
    c = connect()
    try:
        rows = c.execute(
            """SELECT cow_id, breed, latitude, longitude, location_label,
                      herd_id
               FROM cows
               WHERE latitude IS NOT NULL AND longitude IS NOT NULL
               ORDER BY cow_id"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        c.close()


@router.get("/cows/{cow_id}")
def get_cow(cow_id: str):
    c = connect()
    try:
        row = c.execute("SELECT * FROM cows WHERE cow_id=?", (cow_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Cow not registered")
        return dict(row)
    finally:
        c.close()


@router.patch("/cows/{cow_id}/location")
def update_cow_location(cow_id: str, body: dict):
    """§10 — Update cow GPS coordinates and location label."""
    c = connect()
    try:
        row = c.execute(
            "SELECT cow_id FROM cows WHERE cow_id=?", (cow_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Cow not registered")

        lat = body.get("latitude")
        lon = body.get("longitude")
        label = body.get("location_label")

        c.execute(
            """UPDATE cows
               SET latitude=?, longitude=?, location_label=?
               WHERE cow_id=?""",
            (lat, lon, label, cow_id),
        )
        c.commit()
        return {
            "status": "updated",
            "cow_id": cow_id,
            "latitude": lat,
            "longitude": lon,
            "location_label": label,
        }
    finally:
        c.close()
