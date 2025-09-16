# Copyright (C) 2025 Justin Lange
# SPDX-License-Identifier: MIT

from pathlib import Path
from pyld import jsonld
import requests
import json

def _document_loader(url, options={}):
    try:
        response = requests.get(url, headers={'Accept': 'application/ld+json, application/json'})
        response.raise_for_status()
        return {
            'contextUrl': None,
            'document': response.json(),
            'documentUrl': response.url
        }
    except Exception as e:
        raise jsonld.JsonLdError(
            f'Couldnt retrieve a JSON-LD document from URL: {url}',
            'jsonld.LoadDocumentError',
            {'url': url},
            cause=e)

jsonld.set_document_loader(_document_loader)

def build_crate(provenance_data, dataset_meta, author_meta, save_dir):

    # author/creator
    author_name = author_meta.get('name', 'Unknown Author')
    author_id_str = author_name.lower().replace(' ', '-')
    creator_entity = {
        "@id": f"#{author_id_str}",
        "@type": author_meta.get('type', 'Person'),
        "name": author_name,
        "affiliation": {
            "@id": author_meta.get('affiliation', 'https://www.example.com') # placeholder if not provided
        }
    }

    # generate run name
    dataset_name = dataset_meta.get("name", "Unknown Dataset")
    algorithm_name = provenance_data['model_params']['model_name']
    run_name = f"{dataset_name} {algorithm_name} Training Run"

    # dataset
    root_dataset = {
        "@id": "./",
        "@type": "Dataset",
        "name": run_name,
        "identifier": provenance_data['run_id'], # uuid
        "description": "Provenance record for a scikit-learn machine learning experiment.",
        "creator": {"@id": creator_entity["@id"]},
        "dateCreated": provenance_data['start_time'], 
        "license": dataset_meta.get("license", "https://creativecommons.org/publicdomain/zero/1.0/"),
        "datePublished": provenance_data['start_time'], 
        "softwareRequirements": [],
        "hasPart": []
    }

    # auto add software packages/requirements
    software_entities = []
    for name, version in provenance_data['environment']['package_versions'].items():
        package_id = f"https://pypi.org/project/{name}/{version}"
        root_dataset["softwareRequirements"].append({"@id": package_id})
        software_entities.append({
            "@id": package_id,
            "@type": "SoftwareApplication",
            "name": name,
            "version": version
        })

    # input data
    data_info = provenance_data.get('data', {})
    input_dataset_id = dataset_meta.get("identifier", "#input-data")
    input_dataset = {
        "@id": input_dataset_id,
        "@type": "Dataset",
        "name": dataset_meta.get("name", "Input Data"),
        "description": dataset_meta.get("description", "No description provided."),
        "license": dataset_meta.get("license"),
        "variableMeasured": data_info.get("feature_names", []),
        "additionalProperty": [ # added additionalproperty for n_samples and n_features
            {
                "@type": "PropertyValue",
                "name": "n_samples",
                "value": data_info.get("X_shape", [None])[0]
            },
            {
                "@type": "PropertyValue",
                "name": "n_features",
                "value": data_info.get("X_shape", [None, None])[1]
            }
        ]
    }

    # create action
    create_action = {
        "@id": f"#{provenance_data['run_id']}",
        "@type": "CreateAction",
        "name": run_name,
        "identifier": provenance_data['run_id'], # uuuid
        "actionStatus": "https://schema.org/CompletedActionStatus",
        "startTime": provenance_data['start_time'],
        "endTime": provenance_data['end_time'],
        "instrument": {"@id": "skfair"},
        "agent": {"@id": creator_entity["@id"]},
        "object": [{"@id": input_dataset_id}],
        "result": [],
        "additionalProperty": [
            {
                "@type": "PropertyValue",
                "name": "runtime_seconds",
                "value": provenance_data['duration_seconds']
            }
        ]
    }

    # model file
    model_file_info = provenance_data["model_file"]
    model_id = f"#{model_file_info['filename']}"
    model_file = {
        "@id": model_file_info['filename'],
        "@type": "File",
        "name": "Trained Model",
        "contentSize": model_file_info['size_bytes'],
        "sha256": model_file_info['sha256'],
        "encodingFormat": "application/octet-stream",
        "about": {"@id": f"{model_id}-about"},
        "additionalProperty": [
            {
                "@type": "PropertyValue",
                "name": "sha256",
                "value": model_file_info['sha256']
            }
        ]
    }
    
    # model about (config)
    sklearn_id = f"https://pypi.org/project/scikit-learn/{provenance_data['environment']['package_versions']['scikit-learn']}"
    model_about = {
        "@id": f"{model_id}-about",
        "@type": "SoftwareApplication",
        "name": "Model Configuration",
        "description": f"scikit-learn model {provenance_data['model_params']['algorithm_type']}",
        "isBasedOn": [
            {"@id": sklearn_id},
            {"@id": "params.json"}
        ]
    }

    # new model entity
    model_entity = {
        "@id": f"#{provenance_data['model_params']['model_name']}-{provenance_data['run_id']}",
        "@type": "SoftwareApplication",
        "additionalType": "https://w3id.org/ro/terms#Model",
        "name": f"{provenance_data['model_params']['model_name']} v{provenance_data['model_params']['framework_version']}",
        "algorithm": provenance_data['model_params']['algorithm_type'],
        "isBasedOn": [{"@id": sklearn_id}],
        "hasPart": [{"@id": model_file_info['filename']}],
        "about": {"@id": f"{model_id}-about"},
        "additionalProperty": []
    }

    hyperparameters = provenance_data['model_params']['hyperparameters']
    for name, value in hyperparameters.items():
        model_entity["additionalProperty"].append({
            "@type": "PropertyValue",
            "name": name,
            "value": value
        })

    create_action["result"].append({"@id": model_entity['@id']}) # link createaction result to model entity
    root_dataset["hasPart"].append({"@id": model_entity['@id']})

    # new environment entity
    environment_entity = {
        "@id": f"#environment-{provenance_data['run_id']}",
        "@type": "CreativeWork",
        "additionalType": "https://w3id.org/ro/terms#Environment",
        "name": "Execution Environment",
        "additionalProperty": [
            {
                "@type": "PropertyValue",
                "name": "python_version",
                "value": provenance_data['environment']['python_version']
            },
            {
                "@type": "PropertyValue",
                "name": "platform",
                "value": provenance_data['environment']['platform']
            },
            {
                "@type": "PropertyValue",
                "name": "architecture",
                "value": provenance_data['environment']['architecture']
            },
            {
                "@type": "PropertyValue",
                "name": "cpu",
                "value": provenance_data['environment']['cpu']
            }
        ]
    }

    # link createaction instrument to environment entity
    create_action["instrument"] = [{"@id": "skfair"}, {"@id": environment_entity['@id']}]


    # params file
    params_file_info = provenance_data['params_file'] # get info from provenance_data
    params_file = {
        "@id": "params.json",
        "@type": "File",
        "name": "Run Provenance Parameters",
        "encodingFormat": "application/json",
        "contentSize": params_file_info['size_bytes'], # add contentsize
        "sha256": params_file_info['sha256'], # add sha256
        "additionalProperty": [
            {
                "@type": "PropertyValue",
                "name": "sha256",
                "value": params_file_info['sha256']
            }
        ]
    }
    create_action["result"].append({"@id": "params.json"})
    root_dataset["hasPart"].append({"@id": "params.json"})

    # the crate
    crate = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": [
            {
                "@type": "CreativeWork",
                "@id": "ro-crate-metadata.json",
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                "about": {"@id": "./"}
            },
            root_dataset,
            creator_entity,
            {
                "@id": "skfair",
                "@type": "SoftwareApplication",
                "name": "skfair"
            },
            create_action,
            input_dataset,
            model_file,
            model_about,
            params_file,
            model_entity,
            environment_entity
        ] + software_entities
    }

    return crate


def add_metrics_to_crate(crate, metrics, metrics_file_info):
    action = next((item for item in crate["@graph"] if item.get("@type") == "CreateAction"), None)
    root = next((item for item in crate["@graph"] if item.get("@id") == "./"), None)
    if not action or not root:
        return

    metrics_file = {
        "@id": "metrics.json",
        "@type": "File",
        "name": "Evaluation Metrics",
        "encodingFormat": "application/json",
        "about": {"@id": action["result"][0]["@id"]},
        "contentSize": metrics_file_info['size_bytes'],
        "sha256": metrics_file_info['sha256'],
        "additionalProperty": [
            {
                "@type": "PropertyValue",
                "name": "sha256",
                "value": metrics_file_info['sha256']
            }
        ]
    }
    crate["@graph"].append(metrics_file)
    action["result"].append({"@id": "metrics.json"})
    root["hasPart"].append({"@id": "metrics.json"})

    # add metrics to model entity
    model_entity = next((item for item in crate["@graph"] if item.get("additionalType") == "https://w3id.org/ro/terms#Model"), None)
    if model_entity:
        if "additionalProperty" not in model_entity:
            model_entity["additionalProperty"] = []
        elif not isinstance(model_entity["additionalProperty"], list):
            model_entity["additionalProperty"] = [model_entity["additionalProperty"]]
        
        for metric_name, metric_value in metrics.items():
            model_entity["additionalProperty"].append({
                "@type": "PropertyValue",
                "name": f"metric_{metric_name}",
                "value": metric_value
            })


# flatten and compact the crate using pyld
def finalise_crate(crate):
    flattened = jsonld.flatten(crate)
    compacted = jsonld.compact(flattened, "https://w3id.org/ro/crate/1.1/context")
    return compacted