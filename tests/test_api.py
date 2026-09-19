"""Tests for FastAPI endpoints, request handling, provenance contracts, and model states (§13, §14, §16)."""

import pytest
import shutil
from fastapi.testclient import TestClient
from main import app, startup
from app.services.database import connect
from app.services.versioning import promote, record_promotion_status
from config import ROOT, MODELS_DIR

client = TestClient(app)


def test_root_endpoint_metadata():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "model_status" in data
    assert "feature_pipeline_version" in data
    assert data["data_type"] == "synthetic"


def test_no_active_model_graceful_handling(tmp_path, monkeypatch):
    """When models/current/ is unset/unapproved, verify graceful no-active-model behavior."""
    empty_models = tmp_path / "empty_models"
    empty_models.mkdir()
    monkeypatch.setattr("config.MODELS_DIR", empty_models)
    monkeypatch.setattr("main.MODELS_DIR", empty_models)
    startup()

    # 1. Root reports no_active_model
    r_root = client.get("/")
    assert r_root.status_code == 200
    assert r_root.json()["model_status"] == "no_active_model"
    assert r_root.json()["model_version"] is None

    # 2. Register cow
    client.post("/cows", json={"cow_id": "cow_no_model", "parity": 1})

    # 3. Ingest stores reading safely without crashing, reports no_active_model
    r_ingest = client.post("/ingest", json={
        "cow_id": "cow_no_model",
        "milk_yield_l": 15.0,
        "milk_conductivity": 4.5,
        "milk_temp_c": 38.6,
        "timestamp": "2026-02-01T08:00:00",
    })
    assert r_ingest.status_code == 200
    ingest_data = r_ingest.json()
    assert ingest_data["stored"] is True
    assert ingest_data["risk"] is None
    assert ingest_data["model_status"] == "no_active_model"

    # Verify data actually persisted in database
    c = connect()
    row = c.execute("SELECT cow_id, milk_yield_l FROM readings WHERE cow_id='cow_no_model'").fetchone()
    c.close()
    assert row is not None
    assert row[0] == "cow_no_model"

    # 4. Direct prediction query returns 503 rather than corrupted or misleading scores
    r_pred = client.get("/cows/cow_no_model/risk")
    assert r_pred.status_code == 503
    assert "No validated production model" in r_pred.json()["detail"]

    # 5. Alert check skips safely without error
    r_alerts = client.post("/alerts/check")
    assert r_alerts.status_code == 200
    assert r_alerts.json()["status"] == "skipped"
    assert r_alerts.json()["new_alerts_created"] == 0


def test_active_model_prediction_and_provenance(tmp_path, monkeypatch):
    """When a validated model IS approved in current/, verify full prediction contracts."""
    # Set up an approved active model in an isolated directory
    test_models = tmp_path / "models"
    test_models.mkdir()
    # Copy v001 candidate into test_models and mark promoted for testing inference contracts
    src_v001 = MODELS_DIR / "v001"
    if src_v001.exists():
        shutil.copytree(src_v001, test_models / "v001")
        promote("v001", models_dir=test_models)

    monkeypatch.setattr("config.MODELS_DIR", test_models)
    monkeypatch.setattr("main.MODELS_DIR", test_models)
    startup()

    # 1. Register cow
    cow_payload = {
        "cow_id": "cow_active_01",
        "breed": "Jersey",
        "age_years": 4,
        "parity": 2,
        "calving_date": "2026-01-01",
        "vaccination_status": 1,
        "prior_mastitis_flag": 0,
        "herd_id": "active_herd",
    }
    r_cow = client.post("/cows", json=cow_payload)
    assert r_cow.status_code == 200

    # 2. Ingest sensor reading
    read_payload = {
        "cow_id": "cow_active_01",
        "timestamp": "2026-02-01T08:00:00",
        "milk_yield_l": 14.5,
        "milk_conductivity": 4.6,
        "milk_temp_c": 38.6,
        "scc_value": 185000.0,
        "source": "api_test",
    }
    r_ingest = client.post("/ingest", json=read_payload)
    assert r_ingest.status_code == 200
    res = r_ingest.json()
    assert res["stored"] is True
    assert res["risk"] is not None

    risk = res["risk"]
    assert risk["cow_id"] == "cow_active_01"
    assert "risk_score_7d" in risk
    assert "risk_score_14d" in risk
    assert "risk_tier_7d" in risk
    assert "risk_tier_14d" in risk
    assert "top_driver_features" in risk
    assert "top_driver_features_14d" in risk
    assert "recommendations" in risk
    assert "model_version" in risk
    assert "training_data_type" in risk
    assert "prediction_timestamp" in risk
    assert "data_sufficiency_warning" in risk


def test_data_quality_warning_on_out_of_range():
    startup()
    client.post("/cows", json={"cow_id": "cow_bad_temp", "parity": 1})
    payload = {
        "cow_id": "cow_bad_temp",
        "timestamp": "2026-02-01T08:00:00",
        "milk_yield_l": 14.0,
        "milk_conductivity": 4.5,
        "milk_temp_c": 48.0,  # invalid/abnormal
    }
    resp = client.post("/ingest", json=payload)
    assert resp.status_code == 422


def test_alert_deduplication():
    startup()
    c = connect()
    c.execute(
        "INSERT INTO alerts(cow_id, timestamp, risk_score, message, model_version) "
        "VALUES ('cow_alert_01', '2026-02-01T10:00:00', 0.85, 'High mastitis risk. 7-day: 85.0%', 'v001')"
    )
    c.commit()

    from main import maybe_alert
    mock_res = {
        "cow_id": "cow_alert_01",
        "date": "2026-02-01T12:00:00",
        "risk_tier_7d": "High Risk",
        "risk_tier_14d": "High Risk",
        "risk_percent_7d": 88.0,
        "risk_percent_14d": 82.0,
        "risk_score_7d": 0.88,
        "risk_score_14d": 0.82,
        "model_version": "v001",
    }
    created = maybe_alert(mock_res)
    assert created is False, "Duplicate alert was created for the same cow and day!"
    c.close()


def test_drift_summary_endpoint():
    resp = client.get("/drift/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "timestamp" in data
    assert "status" in data
