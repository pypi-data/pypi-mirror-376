# Copyright (C) 2025 Justin Lange
# SPDX-License-Identifier: MIT

import hashlib
import pandas as pd
import numpy as np

# creates a SHA-256 hash of a NumPy array or pandas DataFrame
def hash_data(data):
    if isinstance(data, pd.DataFrame):
        # use pandas hashing, which is consistent for the same data
        return hashlib.sha256(pd.util.hash_pandas_object(data, index=True).values).hexdigest()
    if isinstance(data, np.ndarray):
        # for numpy, convert to bytes in a c-contiguous layout
        return hashlib.sha256(data.tobytes()).hexdigest()
    return None

def capture_data_summary(X, y=None, dataset_meta=None):
    summary = {
        "X_shape": X.shape,
        "X_hash_sha256": hash_data(X),
        "X_type": str(type(X)),
    }
    if hasattr(X, 'columns'):
        summary["feature_names"] = list(X.columns)

    if y is not None:
        summary["y_shape"] = y.shape
        summary["y_hash_sha256"] = hash_data(y)
        summary["y_type"] = str(type(y))

    if dataset_meta:
        summary.update(dataset_meta)

    return summary