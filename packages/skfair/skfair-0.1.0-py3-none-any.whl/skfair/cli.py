# Copyright (C) 2025 Justin Lange
# SPDX-License-Identifier: MIT

import argparse
import json
import pandas as pd
from importlib import import_module
import sys
from pathlib import Path

# add project root to path to allow importing skfair for local usage, if it's not installed using pipy
sys.path.insert(0, str(Path(__file__).parent.parent))

from skfair.wrappers import ProvenanceWrapper

def import_class(class_string):
    module_path, class_name = class_string.rsplit('.', 1)
    module = import_module(module_path)
    return getattr(module, class_name)

def main():
    parser = argparse.ArgumentParser(description="Run a scikit-learn estimator with FAIR provenance capture.")
    
    # subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # fit command
    fit_parser = subparsers.add_parser("fit", help="Fit an estimator.")
    fit_parser.add_argument("--estimator", required=True, help="Full class path of the estimator (e.g., sklearn.ensemble.RandomForestClassifier).")
    fit_parser.add_argument("--params", type=json.loads, default={}, help="JSON string of estimator parameters.")
    fit_parser.add_argument("--data-path", required=True, help="Path to the training data (CSV file).")
    fit_parser.add_argument("--target-column", required=True, help="Name of the target variable column in the data file.")
    fit_parser.add_argument("--dataset-meta", type=json.loads, default={}, help="JSON string or path to a file with dataset metadata.")
    fit_parser.add_argument("--save-dir", help="Directory to save the RO-Crate.")

    args = parser.parse_args()

    if args.command == "fit":
        # estimator
        try:
            estimator_class = import_class(args.estimator)
            estimator = estimator_class(**args.params)
        except (ImportError, AttributeError) as e:
            print(f"Error: Could not import estimator '{args.estimator}'. {e}")
            sys.exit(1)
        except TypeError as e:
            print(f"Error: Invalid parameters for {args.estimator}: {e}")
            sys.exit(1)

        # data
        try:
            data = pd.read_csv(args.data_path)
            X = data.drop(columns=[args.target_column])
            y = data[args.target_column]
        except FileNotFoundError:
            print(f"Error: Data file not found at '{args.data_path}'")
            sys.exit(1)
        except KeyError:
            print(f"Error: Target column '{args.target_column}' not found in data.")
            sys.exit(1)

        # meta data
        dataset_meta = args.dataset_meta
        if isinstance(dataset_meta, str) and Path(dataset_meta).is_file():
             with open(dataset_meta, 'r') as f:
                dataset_meta = json.load(f)

        # provenance wrapper
        wrapped_estimator = ProvenanceWrapper(
            estimator=estimator,
            dataset_meta=dataset_meta,
            author_meta=args.author_meta,
            save_dir=args.save_dir
        )

        print(f"Fitting estimator {args.estimator}...")
        wrapped_estimator.fit(X, y)
        print(f"Provenance RO-Crate saved to: {wrapped_estimator.save_dir}")

if __name__ == "__main__":
    main()