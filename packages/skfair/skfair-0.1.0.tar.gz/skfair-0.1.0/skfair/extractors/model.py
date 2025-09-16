# Copyright (C) 2025 Justin Lange
# SPDX-License-Identifier: MIT

import hashlib
from importlib import metadata


def _sanitise_for_json(obj):
    if isinstance(obj, dict):
        return {k: _sanitise_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitise_for_json(v) for v in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)


def capture_model_params(estimator):
    sklearn_version = None

    try:
        sklearn_version = metadata.version("scikit-learn")
    except metadata.PackageNotFoundError:
        pass

    params = estimator.get_params(deep=True)

    return {
        "model_name": estimator.__class__.__name__,
        "algorithm_type": f"{estimator.__class__.__module__}.{estimator.__class__.__name__}",
        "hyperparameters": _sanitise_for_json(params),
        "framework_name": "scikit-learn",
        "framework_version": sklearn_version,
    }


def get_file_info(file_path):
    sha256 = hashlib.sha256()
    file_size = 0
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
            file_size += len(chunk)
    return {
        "filename": str(file_path.name),
        "size_bytes": file_size,
        "sha256": sha256.hexdigest(),
    }