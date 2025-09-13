"""Kiso experiment configuration schema."""

from importlib.metadata import entry_points
from typing import TYPE_CHECKING

import enoslib as en

if TYPE_CHECKING:
    from importlib.metadata import EntryPoints

_labels_schema: dict = {
    "$$target": "py-obj:kiso.schema.COMMONS_SCHEMA#/$defs/labels",
    "description": "A list of labels identify the resources. The values are strings "
    "that can contain alphanumeric characters, dots, underscores and hyphens",
    "type": "array",
    "title": "Labels Schema",
    "items": {"type": "string", "pattern": "^[a-zA-Z0-9._-]+$"},
    "minItems": 1,
    "uniqueItems": True,
}

COMMONS_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$defs": {
        "labels": _labels_schema,
        "variables": {
            "$$target": "py-obj:kiso.schema.COMMONS_SCHEMA#/$defs/variables",
            "description": "A map of variable name and values. The variable names can "
            "contain alphanumeric or underscore characters",
            "type": "object",
            "title": "Variables Schema",
            "patternProperties": {
                "^[a-zA-Z0-9_]+$": {
                    "oneOf": [
                        {"type": "string"},
                        {"type": "integer"},
                        {"type": "number"},
                    ]
                },
            },
            "additionalProperties": False,
        },
    },
}

SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "title": "Kiso experiment configuration",
    "properties": {
        "name": {"type": "string", "description": "A suitable name for the experiment"},
        "variables": {"$ref": "py-obj:kiso.schema.COMMONS_SCHEMA#/$defs/variables"},
        "sites": {
            "description": "Define all the resources to be provisioned",
            "type": "array",
            "items": {"$ref": "#/$defs/site"},
            "minItems": 1,
        },
        "experiments": {
            "description": "Define all the experiments to be executed",
            "type": "array",
            "items": {"$ref": "#/$defs/experiment"},
            "minItems": 1,
        },
        "software": {
            "description": "Software to be installed on the resources",
            "type": "object",
            "properties": {
                "docker": {
                    "description": "Specify on which resources the Docker runtime "
                    "should be installed",
                    "type": "object",
                    "properties": {
                        "labels": {
                            "$ref": "py-obj:kiso.schema.COMMONS_SCHEMA#/$defs/labels"
                        },
                        "version": {"type": "string"},
                    },
                    "required": ["labels"],
                    "additionalProperties": False,
                },
                "apptainer": {
                    "description": "Specify on which resources the Apptainer runtime "
                    "should be installed",
                    "type": "object",
                    "properties": {
                        "labels": {
                            "$ref": "py-obj:kiso.schema.COMMONS_SCHEMA#/$defs/labels"
                        },
                        "version": {"type": "string"},
                    },
                    "required": ["labels"],
                    "additionalProperties": False,
                },
            },
        },
        "deployment": {
            "description": "Workload management system to be installed on the "
            "resources",
            "type": "object",
            "properties": {
                "htcondor": {
                    "description": "Specify how and on which resources HTCondor "
                    "should be installed",
                    "type": "array",
                    "items": {"$ref": "#/$defs/htcondor"},
                    "minItems": 1,
                }
            },
            "additionalProperties": False,
        },
    },
    "required": ["name", "sites", "experiments"],
    "additionalProperties": False,
    "$defs": {
        "site": {
            "title": "Site Definition",
            "oneOf": [],
        },
        "experiment": {
            "title": "Experiment Definition",
            "oneOf": [],
        },
        "htcondor": {
            "description": "Specify how and on which resources HTCondor "
            "should be installed",
            "type": "object",
            "properties": {
                "kind": {
                    "description": "Specify which resource will have the "
                    "central manager and it's configuration",
                    "type": "string",
                    "enum": ["central-manager", "execute", "submit", "personal"],
                },
                "labels": {"$ref": "py-obj:kiso.schema.COMMONS_SCHEMA#/$defs/labels"},
                "config-file": {"type": "string"},
            },
            "required": ["kind", "labels"],
            "additionalProperties": False,
        },
    },
}


_labels_schema = _labels_schema.copy()
_labels_schema["description"] = (
    "A list of labels identify the resources. The values are "
    "strings that can't start with 'kiso.' and can contain alphanumeric characters, "
    "dots, underscores and hyphens"
)
_labels_schema["items"] = _labels_schema["items"].copy()
_labels_schema["items"]["pattern"] = "^(?!kiso\\.)[a-zA-Z0-9._-]+$"


if hasattr(en, "Vagrant"):
    from enoslib.infra.enos_vagrant.schema import SCHEMA as VAGRANT_SCHEMA

    # $$target required in docs
    # https://sphinx-jsonschema.readthedocs.io/en/latest/schemakeywords.html#target
    VAGRANT_SCHEMA["$$target"] = "py-obj:kiso.schema.VAGRANT_SCHEMA"
    VAGRANT_SCHEMA["properties"]["kind"] = {"const": "vagrant"}
    VAGRANT_SCHEMA["definitions"]["machine"]["properties"]["roles"] = _labels_schema
    VAGRANT_SCHEMA["definitions"]["network"]["properties"]["roles"] = _labels_schema
    SCHEMA["$defs"]["site"]["oneOf"].append(
        {
            "allOf": [
                {"required": ["kind"]},
                {"$ref": "py-obj:kiso.schema.VAGRANT_SCHEMA"},
            ]
        }
    )

if hasattr(en, "CBM"):
    from enoslib.infra.enos_chameleonkvm.schema import SCHEMA as CBM_SCHEMA

    CBM_SCHEMA["$$target"] = "py-obj:kiso.schema.CBM_SCHEMA"
    CBM_SCHEMA["title"] = "Chameleon Configuration Schema"
    CBM_SCHEMA["properties"]["kind"] = {"const": "chameleon"}
    CBM_SCHEMA["machine"]["properties"]["roles"] = _labels_schema
    SCHEMA["$defs"]["site"]["oneOf"].append(
        {
            "allOf": [
                {"required": ["kind"]},
                {"$ref": "py-obj:kiso.schema.CBM_SCHEMA"},
            ]
        }
    )

if hasattr(en, "ChameleonEdge"):
    from enoslib.infra.enos_chameleonedge.schema import SCHEMA as CHAMELEON_EDGE_SCHEMA

    CHAMELEON_EDGE_SCHEMA["$$target"] = "py-obj:kiso.schema.CHAMELEON_EDGE_SCHEMA"
    CHAMELEON_EDGE_SCHEMA["title"] = "Chameleon Edge Configuration Schema"
    CHAMELEON_EDGE_SCHEMA["properties"]["kind"] = {"const": "chameleon-edge"}
    CHAMELEON_EDGE_SCHEMA["deviceCluster"]["properties"]["roles"] = _labels_schema
    CHAMELEON_EDGE_SCHEMA["device"]["properties"]["roles"] = _labels_schema
    CHAMELEON_EDGE_SCHEMA["network"]["properties"]["roles"] = _labels_schema
    SCHEMA["$defs"]["site"]["oneOf"].append(
        {
            "allOf": [
                {"required": ["kind"]},
                {"$ref": "py-obj:kiso.schema.CHAMELEON_EDGE_SCHEMA"},
            ]
        }
    )

if hasattr(en, "Fabric"):
    from enoslib.infra.enos_fabric.schema import SCHEMA as FABRIC_SCHEMA

    FABRIC_SCHEMA["$$target"] = "py-obj:kiso.schema.FABRIC_SCHEMA"
    FABRIC_SCHEMA["properties"]["kind"] = {"const": "fabric"}
    FABRIC_SCHEMA["definitions"]["machine"]["properties"]["roles"] = _labels_schema
    SCHEMA["$defs"]["site"]["oneOf"].append(
        {
            "allOf": [
                {"required": ["kind"]},
                {"$ref": "py-obj:kiso.schema.FABRIC_SCHEMA"},
            ]
        }
    )


def _get_experiment_kinds() -> list[dict[str, str]]:
    all_eps: dict | EntryPoints = entry_points()
    if isinstance(all_eps, dict):
        all_eps = all_eps.get("kiso.experiment", [])
    else:
        all_eps = all_eps.select(group="kiso.experiment")

    # The set is required because entry_points() can return the same EntryPoint
    # multiple times when a package is installed as an editable install
    _kind_schemas = set()
    kind_schemas = []
    for ep in all_eps:
        if f"{ep.value}.SCHEMA" not in _kind_schemas:
            ep.load().SCHEMA["$$target"] = f"py-obj:{ep.value}.SCHEMA"
            kind_schemas.append({"$ref": f"py-obj:{ep.value}.SCHEMA"})
            _kind_schemas.add(f"{ep.value}.SCHEMA")

    return kind_schemas


SCHEMA["$defs"]["experiment"]["oneOf"] = _get_experiment_kinds()
