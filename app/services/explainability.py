import numpy as np

def top_drivers(row, model):
    X = row
    try:
        import shap
        vals = shap.TreeExplainer(model).shap_values(X)
        vals = vals[0] if np.ndim(vals) > 1 else vals
        pairs = sorted(zip(X.columns, vals), key=lambda x: abs(float(x[1])), reverse=True)[:5]
        return [{"feature": f, "impact": round(float(v), 4)} for f, v in pairs]
    except Exception:
        pairs = sorted(zip(X.columns, model.feature_importances_), key=lambda x: float(x[1]), reverse=True)[:5]
        return [{"feature": f, "impact": round(float(v), 4)} for f, v in pairs]
