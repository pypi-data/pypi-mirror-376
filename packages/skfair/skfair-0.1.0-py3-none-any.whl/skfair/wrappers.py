# Copyright (C) 2025 Justin Lange
# SPDX-License-Identifier: MIT

import uuid
import datetime
import joblib
import os
import json
from pathlib import Path

from sklearn.base import is_classifier, is_regressor
from sklearn.utils.metaestimators import available_if

from .extractors import env as env_extractor
from .extractors import model as model_extractor
from .extractors import data as data_extractor
from .extractors import metrics as metrics_extractor
from .emitters import rocrate as rocrate_emitter

class ProvenanceWrapper:
    """
    A meta-estimator that wraps a scikit-learn estimator to capture
    FAIR-compliant provenance metadata.
    """

    def __init__(self, estimator, *, dataset_meta=None, author_meta=None, eval_plan=None, save_dir=None):
        self.estimator = estimator
        self.dataset_meta = dataset_meta or {}
        self.author_meta = author_meta or {}
        self.eval_plan = eval_plan or {}
        self.save_dir = Path(save_dir) if save_dir else Path(f"crates/run-{datetime.datetime.now().isoformat()}")

        # internal state
        self._run_id = str(uuid.uuid4())
        self._crate_meta = {}
        self._is_fitted = False

    def get_params(self, deep=True):
        return self.estimator.get_params(deep)

    def set_params(self, **params):
        self.estimator.set_params(**params)
        return self

    def fit(self, X, y=None, **fit_params):
        print("DEBUG: fitting the model")
        """
        Fits the wrapped estimator and captures provenance.
        """
        start_time = datetime.datetime.now(datetime.timezone.utc)

        # make sure final directory exists
        self.save_dir.mkdir(parents=True, exist_ok=True)

        # capture environment, estimator, and data info
        env_info = env_extractor.capture_environment()
        model_info = model_extractor.capture_model_params(self.estimator)
        data_info = data_extractor.capture_data_summary(X, y, self.dataset_meta)

        self.estimator.fit(X, y, **fit_params)
        self._is_fitted = True

        end_time = datetime.datetime.now(datetime.timezone.utc)
        duration = (end_time - start_time).total_seconds()

        # post-fit capture
        # persist model
        model_path = self.save_dir / "model.joblib"
        joblib.dump(self.estimator, model_path)
        model_file_info = model_extractor.get_file_info(model_path)

        # sum and write params
        provenance_data = {
            "run_id": self._run_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "environment": env_info,
            "model_params": model_info,
            "data": data_info,
            "model_file": model_file_info,
        }

        params_path = self.save_dir / "params.json"
        with open(params_path, 'w') as f:
            json.dump(provenance_data, f, indent=4)
        provenance_data['params_file'] = model_extractor.get_file_info(params_path)

        # build ro-crate
        self._crate_meta = rocrate_emitter.build_crate(
            provenance_data,
            self.dataset_meta,
            self.author_meta,
            self.save_dir
        )
        finalised_crate = rocrate_emitter.finalise_crate(self._crate_meta)
        crate_path = self.save_dir / "ro-crate-metadata.json"
        with open(crate_path, 'w') as f:
            json.dump(finalised_crate, f, indent=4)

        return self

    @available_if(lambda self: hasattr(self.estimator, "predict"))
    def predict(self, X):
        return self.estimator.predict(X)

    @available_if(lambda self: hasattr(self.estimator, "predict_proba"))
    def predict_proba(self, X):
        return self.estimator.predict_proba(X)

    @available_if(lambda self: hasattr(self.estimator, "score"))
    def score(self, X, y=None):
        return self.estimator.score(X, y)

    def evaluate(self, X, y):
        print("DEBUG: eval model") 
        
        if not self._is_fitted:
            raise RuntimeError("Cannot evaluate before fitting.")

        metrics = metrics_extractor.calculate_metrics(
            self.estimator, X, y, self.eval_plan.get("metrics", [])
        )

        metrics_path = self.save_dir / "metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=4)
        metrics_file_info = model_extractor.get_file_info(metrics_path)

        # update ro-crate with metrics
        rocrate_emitter.add_metrics_to_crate(self._crate_meta, metrics, metrics_file_info)
        finalised_crate = rocrate_emitter.finalise_crate(self._crate_meta)
        crate_path = self.save_dir / "ro-crate-metadata.json"
        with open(crate_path, 'w') as f:
            json.dump(finalised_crate, f, indent=4)

        return metrics

    @property
    def _estimator_type(self):
        return self.estimator._estimator_type
