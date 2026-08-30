# Bovine Mastitis Forecasting V3

An AI/ML + IoT prototype for forecasting bovine mastitis risk at the individual-cow and herd levels using daily milk measurements and accumulated animal history.

> **Prototype status:** The current training data is synthetic. The system demonstrates the complete forecasting workflow, but it is not clinically validated and must not be used as a veterinary diagnosis.

---

## 1. Overview

Bovine mastitis is a major dairy-animal health problem that can reduce milk production and milk quality and increase treatment costs.

This prototype provides an early-warning system by combining:

- IoT sensor readings
- Historical cow-level observations
- Somatic Cell Count (SCC)
- Machine Learning
- Explainable AI
- Risk categorization
- Recommendations
- Herd-level monitoring

The current prototype focuses on the **cow's own accumulated history**. Farm-management information is not required for the current demonstration.

---

## 2. Current Prototype Workflow

For each cow, daily readings are stored permanently using a unique `cow_id`.

When a new reading is submitted, the backend:

1. Stores the new reading.
2. Retrieves the complete history of that cow.
3. Aggregates observations by calendar day.
4. Carries forward the latest known SCC when SCC is not measured every day.
5. Applies fixed healthy prototype baselines for features that are not currently collected.
6. Builds rolling 3-day and 7-day statistical and trend features.
7. Runs the trained 7-day XGBoost model.
8. Runs the trained 14-day XGBoost model.
9. Produces risk percentages and risk categories.
10. Generates explainability information and recommendations.
11. Returns the latest result immediately from `/ingest`.

The endpoint:

```text
GET /cows/{cow_id}/risk-history
