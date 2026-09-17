from fastapi import APIRouter, HTTPException
from app.services.database import connect
router=APIRouter()

@router.post("/cows")
def create_cow(cow:dict):
    if "cow_id" not in cow or "parity" not in cow: raise HTTPException(400,"cow_id and parity required")
    if not str(cow["cow_id"]).strip(): raise HTTPException(400,"cow_id cannot be empty")
    try:
        parity = int(cow["parity"])
    except (TypeError, ValueError):
        raise HTTPException(400, "parity must be an integer")
    if parity < 1: raise HTTPException(400, "parity must be >= 1")
    c=connect()
    c.execute("""INSERT OR REPLACE INTO cows(cow_id,breed,age_years,parity,calving_date,vaccination_status,prior_mastitis_flag,herd_id)
                 VALUES(?,?,?,?,?,?,?,?)""",
              (cow["cow_id"],cow.get("breed"),cow.get("age_years"),parity,cow.get("calving_date"),
               cow.get("vaccination_status",1),cow.get("prior_mastitis_flag",0),cow.get("herd_id","demo_herd_01")))
    c.commit(); c.close(); return {"status":"created","cow_id":cow["cow_id"]}

@router.get("/cows")
def list_cows():
    c=connect(); rows=c.execute("SELECT * FROM cows ORDER BY cow_id").fetchall(); c.close()
    return [dict(x) for x in rows]

@router.get("/cows/{cow_id}")
def get_cow(cow_id):
    c=connect(); row=c.execute("SELECT * FROM cows WHERE cow_id=?", (cow_id,)).fetchone(); c.close()
    if not row: raise HTTPException(404, "Cow not registered")
    return dict(row)
