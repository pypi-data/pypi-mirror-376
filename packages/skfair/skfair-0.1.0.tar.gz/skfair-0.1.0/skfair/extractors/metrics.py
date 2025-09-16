# Copyright (C) 2025 Justin Lange
# SPDX-License-Identifier: MIT

from sklearn import metrics as sk_metrics

SUPPORTED_METRICS = {
    "accuracy": sk_metrics.accuracy_score,
    "f1": lambda y_true, y_pred: sk_metrics.f1_score(y_true, y_pred, average='macro'),
    "roc_auc": sk_metrics.roc_auc_score,
    # extend..
}

def calculate_metrics(estimator, X, y, metric_names):
    results = {}
    y_pred = estimator.predict(X)

    for name in metric_names:
        if name in SUPPORTED_METRICS:
            try:
                if name == "roc_auc":
                    # requires prob scores
                    y_proba = estimator.predict_proba(X)[:, 1]
                    results[name] = SUPPORTED_METRICS[name](y, y_proba)
                else:
                    results[name] = SUPPORTED_METRICS[name](y, y_pred)
            except Exception as e:
                results[name] = f"Error: {e}"
        else:
            results[name] = "Unsupported metric"
    return results