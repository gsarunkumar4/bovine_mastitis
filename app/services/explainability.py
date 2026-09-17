import numpy as np

_explainer_cache = {}


def _get_explainer(model):
    key = id(model)
    if key not in _explainer_cache:
        import shap
        _explainer_cache[key] = shap.TreeExplainer(model)
    return _explainer_cache[key]


def top_drivers(row, model, n=5):
    X = row
    try:
        vals = _get_explainer(model).shap_values(X)
        vals = vals[0] if np.ndim(vals) > 1 else vals
        pairs = sorted(zip(X.columns, vals), key=lambda x: abs(float(x[1])), reverse=True)[:n]
        return [{"feature": f, "impact": round(float(v), 4)} for f, v in pairs]
    except Exception:
        # SHAP not installed, or an incompatible model type -- fall back to
        # the model's own (less precise, but always available) global
        # feature importances rather than failing the whole prediction.
        importances = getattr(model, "feature_importances_", None)
        if importances is None:
            return []
        pairs = sorted(zip(X.columns, importances), key=lambda x: float(x[1]), reverse=True)[:n]
        return [{"feature": f, "impact": round(float(v), 4)} for f, v in pairs]
