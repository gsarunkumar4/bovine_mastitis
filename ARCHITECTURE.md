# Architecture — Daily Accumulating Animal History

```text
ESP32 / sensor source
   |
   | daily cow_id + milk yield + conductivity + milk temperature
   | optional periodic SCC
   v
FastAPI /ingest
   |
   +--> SQLite readings table (permanent history)
   |
   v
Daily aggregation per cow
   |
   v
3-day / 7-day rolling features
   |
   +--> 7-day XGBoost risk
   +--> 14-day XGBoost risk
   |
   v
Dashboard
   +--> latest animal risk
   +--> daily risk history
   +--> herd ranking
   +--> recommendations
   +--> high-risk alerts
```

The current prototype intentionally does not require farm-management inputs. Missing SCC is handled by carrying forward the latest available SCC; if none has ever been supplied, a prototype baseline is used. Farm/environment variables can be added later without changing the daily-history storage design.


## Current prototype data policy

The complete ML signal set is retained. The current hardware workflow only supplies direct readings for milk yield, milk conductivity and milk temperature, with SCC supplied periodically when available. Farm/behaviour fields remain model features but are automatically assigned fixed healthy prototype baselines until real farm inputs are added.

Every ingested reading is stored by cow and calendar day. Daily aggregation creates the rolling 3-day and 7-day features. The `/ingest` endpoint immediately recomputes the 7-day and 14-day forecast using the full history available up to that sample. `/cows/{cow_id}/risk-history` exposes the day-by-day forecast trajectory.
