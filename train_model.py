import json
from pathlib import Path
import joblib, numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, confusion_matrix, recall_score, precision_score, f1_score, average_precision_score
from xgboost import XGBClassifier
from app.services.features import engineer, SIGNALS, FIXED_GOOD_VALUES


def cow_split(df):
    labels = df.groupby("cow_id")["target_7d"].max().reset_index()
    pos = labels.loc[labels.target_7d == 1, "cow_id"].to_numpy()
    neg = labels.loc[labels.target_7d == 0, "cow_id"].to_numpy()
    rng = np.random.default_rng(2026); rng.shuffle(pos); rng.shuffle(neg)
    def split(a):
        n = len(a); return a[:int(.70*n)], a[int(.70*n):int(.85*n)], a[int(.85*n):]
    pt, pv, pe = split(pos); nt, nv, ne = split(neg)
    return (
        df[df.cow_id.isin(set(np.r_[pt, nt]))],
        df[df.cow_id.isin(set(np.r_[pv, nv]))],
        df[df.cow_id.isin(set(np.r_[pe, ne]))],
    )


def choose_threshold(y, p, target_recall=.80):
    best = None
    for t in np.linspace(.01, .99, 197):
        pred = (p >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
        rec = tp / max(1, tp + fn); spec = tn / max(1, tn + fp); prec = tp / max(1, tp + fp)
        item = (t, rec, spec, prec)
        if rec >= target_recall and (best is None or (spec, prec, rec) > (best[2], best[3], best[1])):
            best = item
    if best:
        return best
    fallback = (0, 0, 0, 0)
    for t in np.linspace(.01, .99, 197):
        pred = (p >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
        rec = tp / max(1, tp + fn); spec = tn / max(1, tn + fp); prec = tp / max(1, tp + fp)
        if (rec, spec, prec) > (fallback[1], fallback[2], fallback[3]):
            fallback = (t, rec, spec, prec)
    return fallback


def evaluate(y, p, t):
    pred = (p >= t).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "auc": float(roc_auc_score(y, p)),
        "average_precision": float(average_precision_score(y, p)),
        "threshold": float(t),
        "sensitivity_recall": float(recall_score(y, pred, zero_division=0)),
        "specificity": float(tn / max(1, tn + fp)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def train_horizon(df, target_col, out_name, split_data):
    train, val, test = split_data
    features = [c for c in df.columns if c not in [
        "cow_id", "timestamp", "target_7d", "target_14d", "event_onset_day",
        "breed", "calving_date", "herd_id"
    ]]
    Xtr, ytr = train[features], train[target_col]
    Xv, yv = val[features], val[target_col]
    Xte, yte = test[features], test[target_col]

    baseline = LogisticRegression(max_iter=1000, class_weight="balanced", solver="liblinear").fit(Xtr, ytr)
    base_p = baseline.predict_proba(Xte)[:, 1]

    pos = max(1, int(ytr.sum())); neg = max(1, int((ytr == 0).sum()))
    model = XGBClassifier(
        n_estimators=120, max_depth=4, learning_rate=.04, subsample=.9,
        colsample_bytree=.9, objective="binary:logistic", eval_metric="logloss",
        scale_pos_weight=neg/pos, random_state=2026, n_jobs=4, tree_method="hist"
    )
    model.fit(Xtr, ytr)
    threshold, vr, vs, vp = choose_threshold(yv, model.predict_proba(Xv)[:, 1], .80)
    result = evaluate(yte, model.predict_proba(Xte)[:, 1], threshold)
    result.update({
        "baseline_logistic_auc": float(roc_auc_score(yte, base_p)),
        "forecast_horizon_days": 7 if target_col == "target_7d" else 14,
        "window_type": "calendar-time 3D/7D",
        "validation_recall": float(vr),
        "validation_specificity": float(vs),
        "validation_precision": float(vp),
        "split": "cow-level stratified",
        "data_type": "synthetic",
        "signals_used": SIGNALS,
        "farm_information_used": False,
        "prototype_fixed_baselines": FIXED_GOOD_VALUES,
    })
    joblib.dump(model, f"models/{out_name}.joblib")
    return features, result


base_df = pd.read_csv("data/cleaned.csv")
# Keep every original ML signal. The current prototype does not collect farm
# information, so these six farm/behaviour signals use fixed healthy baselines.
for col, value in FIXED_GOOD_VALUES.items():
    base_df[col] = value

df = engineer(base_df)
train, val, test = cow_split(df)
Path("models").mkdir(exist_ok=True)
features, result7 = train_horizon(df, "target_7d", "mastitis_model_7d", (train, val, test))
_, result14 = train_horizon(df, "target_14d", "mastitis_model_14d", (train, val, test))

joblib.dump(features, "models/feature_cols.joblib")
metrics = {"7d": result7, "14d": result14, "signals_used": SIGNALS, "farm_information_used": False, "prototype_fixed_baselines": FIXED_GOOD_VALUES}
Path("models/metrics.json").write_text(json.dumps(metrics, indent=2))
# Backward-compatible artifact name for older code/users.
joblib.dump(joblib.load("models/mastitis_model_7d.joblib"), "models/mastitis_model.joblib")
print(json.dumps(metrics, indent=2))
