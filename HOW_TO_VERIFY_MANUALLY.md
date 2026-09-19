# How to manually verify the ML is working

This checks the REAL trained model through your REAL running server and
dashboard -- nothing here is pre-computed or faked. You feed in raw sensor
readings only; the server computes the risk scores live.

Two ready-made datasets are included at the project root:

- `10_cows_WITH_mastitis.csv`    -- 10 cows that developed confirmed mastitis, 146 days of daily readings each
- `10_cows_WITHOUT_mastitis.csv` -- 10 healthy cows, 146 days of daily readings each

Both contain ONLY raw sensor/manual-entry fields (milk yield, conductivity,
temperature, SCC, activity, rumination, etc.) plus basic cow metadata
(breed, age, parity, etc.). There is no risk score, tier, or mastitis label
in either file -- if there were, ingesting them would be feeding the answer
back into the model instead of testing it.

## Step 1 -- Start the API server

```bash
cd Bovine_mastitis_V4
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Leave this running. Check `http://127.0.0.1:8000/docs` loads in a browser
to confirm it's up.

## Step 2 -- Start the dashboard (separate terminal)

```bash
cd Bovine_mastitis_V4/dashboard
python -m http.server 5500
```

Open `http://127.0.0.1:5500`. In the dashboard's settings, confirm the API
URL field says `http://127.0.0.1:8000` (it defaults to this).

## Step 3 -- Feed in the data (a third terminal)

```bash
cd Bovine_mastitis_V4
pip install requests pandas     # if not already installed
python ingest_to_server.py 10_cows_WITH_mastitis.csv
python ingest_to_server.py 10_cows_WITHOUT_mastitis.csv
```

This posts every day of every cow's history to your running server via real
HTTP, in order, exactly like a sensor gateway would. It prints each cow's
final risk tier as it finishes.

## Step 4 -- Check the dashboard

Refresh the dashboard. All 20 cows should now appear with live risk scores
and tiers. What to look for:

- The 10 `_WITH_mastitis` cows should show risk climbing into
  **Moderate/High Risk** in the days before their known issue (you don't
  have the exact onset date in the CSV on purpose -- that's the label you're
  checking the model against; if you want it for comparison, ask and I can
  give you the ground-truth onset days for these specific cows separately).
- The 10 `_WITHOUT_mastitis` cows should mostly stay in **No/Low Risk**
  throughout. A rare cow drifting into Moderate is normal (the model isn't
  100% precise -- see `IMPLEMENTATION_REPORT.md` for its measured
  precision/recall) -- it becomes a problem only if most or all healthy
  cows show High Risk.
- Click into an individual cow to see the SHAP driver features behind its
  score (e.g. "SCC trending up", "milk yield dropping").

## Alternative: skip the dashboard, just check the numbers

If you only want the raw predicted numbers (no browser needed):

```bash
python predict_from_raw_csv.py 10_cows_WITH_mastitis.csv results_mastitis.csv
python predict_from_raw_csv.py 10_cows_WITHOUT_mastitis.csv results_healthy.csv
```

This uses an isolated throwaway database (won't touch anything from Step 1-3)
and writes the model's fresh predictions to the given CSV. Takes a few
minutes for all 10 cows x 146 days each -- run it, don't Ctrl-C it early.
