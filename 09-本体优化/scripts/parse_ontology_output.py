#!/usr/bin/env python3
"""Generate human-readable and machine-readable views for an ontology output."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import yaml


RESEARCH_TARGET_TYPES = ["Industry", "Segment", "Company", "Product", "Material", "Asset"]
TEMPLATE_TYPES = ["StateVariable", "StateVariablePropagation"]
REASONING_INSTANCE_TYPES = [
    "Event",
    "StateHypothesis",
    "Signal",
    "JudgmentOutput",
    "AssetImpact",
    "InvestmentThesis",
]
SUMMARY_VIEW_TYPES = {
    "state_variables": "StateVariable",
    "state_observations": "StateVariableObservation",
    "propagation_templates": "StateVariablePropagation",
    "hypotheses": "StateHypothesis",
    "signals": "Signal",
    "events": "Event",
    "judgment_outputs": "JudgmentOutput",
    "asset_impacts": "AssetImpact",
    "investment_theses": "InvestmentThesis",
}
SIGNAL_RELATION_ROLES = {
    "supportsHypothesis": "支持",
    "tracksHypothesis": "跟踪",
    "weakensHypothesis": "削弱",
    "blocksHypothesis": "阻断",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", type=Path)
    parser.add_argument("--core-schema-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(value.rstrip() + "\n")


def md(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\n", " ").replace("|", "\\|")
    return " ".join(text.split())


def flatten_module(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if not isinstance(value, dict):
        return []
    rows: list[dict[str, Any]] = []
    for item in value.values():
        if isinstance(item, list):
            rows.extend(entry for entry in item if isinstance(entry, dict))
    return rows


def normalize_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    evidence = bundle.get("evidence", {}) if isinstance(bundle.get("evidence"), dict) else {}
    governance = bundle.get("governance", {}) if isinstance(bundle.get("governance"), dict) else {}
    handoff = bundle.get("optimization_handoff", {}) if isinstance(bundle.get("optimization_handoff"), dict) else {}
    reasoning = bundle.get("reasoning", {}) if isinstance(bundle.get("reasoning"), dict) else {}

    ontology = {
        "ontology_metadata": bundle.get("ontology_manifest", {}),
        "concept_layer": bundle.get("concepts", {}),
        "objects": flatten_module(bundle.get("objects", {})),
        "relations": flatten_module(bundle.get("relations", {})),
        "source_documents": evidence.get("source_documents", []),
        "evidence_claims": evidence.get("evidence_claims", []),
        "state_observations": evidence.get("state_observations", []),
        "evidence_matrix": evidence.get("evidence_matrix", []),
        "quality_checks": governance.get("quality_checks", []),
        "missing_evidence": governance.get("missing_evidence", []),
        "human_review_required": governance.get("human_review_required", []),
        "unresolved_objects": governance.get("unresolved_objects", []),
        "unresolved_relations": governance.get("unresolved_relations", []),
        "richness_retention": governance.get("richness_retention", {}),
        "suggested_actions": handoff.get("change_requests", []),
    }
    for key in [
        "state_variables",
        "propagation_templates",
        "hypotheses",
        "signals",
        "events",
        "judgment_outputs",
        "asset_impacts",
        "investment_theses",
        "blocking_conditions",
        "scenario_paths",
        "asset_impact_clues",
    ]:
        ontology[key] = reasoning.get(key, [])
    return ontology


def shorten(value: Any, limit: int = 120) -> str:
    text = md(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def count_by(items: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(item.get(key, "")) for item in items).items()))


def object_label(obj: dict[str, Any] | None) -> str:
    if not obj:
        return ""
    fields = obj.get("fields", {})
    for key in (
        "name",
        "title",
        "templateName",
        "propagationLogic",
        "hypothesisContent",
        "judgmentContent",
        "observedValue",
        "description",
    ):
        if fields.get(key):
            return shorten(fields[key], 100)
    return obj.get("id", "")


def table(headers: list[str], rows: Iterable[Iterable[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(md(cell) for cell in row) + " |")
    return "\n".join(lines)


def list_or_none(values: Iterable[str]) -> str:
    cleaned = [value for value in values if value]
    return "、".join(cleaned) if cleaned else "无"


def mermaid_id(value: str) -> str:
    return "n" + "".join(character for character in value if character.isalnum())


def mermaid_label(value: Any) -> str:
    return md(value).replace('"', "'")


def relation_link(
    relation: dict[str, Any],
    objects_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source = objects_by_id.get(relation.get("sourceId", ""))
    target = objects_by_id.get(relation.get("targetId", ""))
    return {
        "relation_id": relation.get("id", ""),
        "type": relation.get("type", ""),
        "source_id": relation.get("sourceId", ""),
        "source_label": object_label(source),
        "target_id": relation.get("targetId", ""),
        "target_label": object_label(target),
        "record_status": relation.get("recordStatus", ""),
        "evidence_level": relation.get("evidenceLevel", ""),
    }


def main() -> None:
    args = parse_args()
    source = load_json(args.input_json)
    if "optimized_ontology" not in source and "optimization_delta" in source:
        raise SystemExit(
            "input contains optimization_delta but no optimized_ontology; "
            "run scripts/apply_optimization_delta.py first and parse the merged full output"
        )
    if "optimized_ontology" in source:
        ontology = source["optimized_ontology"]
    elif "ontology_bundle" in source:
        ontology = normalize_bundle(source["ontology_bundle"])
    else:
        raise SystemExit("input JSON must contain optimized_ontology or ontology_bundle")
    report = source.get("optimization_report", {})

    object_schema = load_yaml(args.core_schema_dir / "objects.yaml")
    relation_schema = load_yaml(args.core_schema_dir / "relations.yaml")
    action_schema = load_yaml(args.core_schema_dir / "actions.yaml")

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    curated_template_view_exists = True

    objects = ontology.get("objects", [])
    relations = ontology.get("relations", [])
    objects_by_id = {obj["id"]: obj for obj in objects}
    outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for relation in relations:
        outgoing[relation.get("sourceId", "")].append(relation)
        incoming[relation.get("targetId", "")].append(relation)

    def targets(source_id: str, relation_type: str) -> list[dict[str, Any]]:
        return [
            objects_by_id[relation["targetId"]]
            for relation in outgoing.get(source_id, [])
            if relation.get("type") == relation_type and relation.get("targetId") in objects_by_id
        ]

    def sources(target_id: str, relation_type: str) -> list[dict[str, Any]]:
        return [
            objects_by_id[relation["sourceId"]]
            for relation in incoming.get(target_id, [])
            if relation.get("type") == relation_type and relation.get("sourceId") in objects_by_id
        ]

    def anchors(object_id: str) -> list[dict[str, Any]]:
        anchor_types = {
            "observedOn",
            "companyBelongsToIndustry",
            "companyParticipatesInSegment",
            "productBelongsToSegment",
            "productProducedBy",
            "materialBelongsToIndustry",
            "materialUsedInSegment",
            "companyLinkedToAsset",
            "assetLinkedToIndustry",
            "judgmentAnchoredOn",
            "thesisAnchoredOn",
        }
        links = []
        for relation in outgoing.get(object_id, []):
            if relation.get("type") in anchor_types:
                links.append(relation_link(relation, objects_by_id))
        return links

    object_counts = count_by(objects, "type")
    relation_counts = count_by(relations, "type")
    governance_counts = count_by(objects, "governanceLayer")
    object_status_counts = count_by(objects, "recordStatus")
    relation_status_counts = count_by(relations, "recordStatus")
    object_evidence_counts = count_by(objects, "evidenceLevel")
    relation_evidence_counts = count_by(relations, "evidenceLevel")

    object_axioms: list[dict[str, Any]] = []
    for type_name, spec in object_schema.get("object_types", {}).items():
        object_axioms.append(
            {
                "type": type_name,
                "zh_name": spec.get("zh_name", ""),
                "category": spec.get("category", ""),
                "description": spec.get("description", ""),
                "managed_by": spec.get("managed_by", ""),
                "used_in_v4": type_name in object_counts,
                "instance_count": object_counts.get(type_name, 0),
                "fields": [
                    {
                        "name": field_name,
                        "zh_name": field_spec.get("zh_name", ""),
                        "type": field_spec.get("type", ""),
                        "required": field_spec.get("required", False),
                    }
                    for field_name, field_spec in spec.get("fields", {}).items()
                ],
            }
        )

    relation_axioms: list[dict[str, Any]] = []
    for type_name, spec in relation_schema.get("relation_types", {}).items():
        relation_axioms.append(
            {
                "type": type_name,
                "zh_name": spec.get("zh_name", ""),
                "group": spec.get("group", ""),
                "source_types": spec.get("source_types", []),
                "target_types": spec.get("target_types", []),
                "cardinality": spec.get("cardinality", ""),
                "description": spec.get("description", ""),
                "used_in_v4": type_name in relation_counts,
                "instance_count": relation_counts.get(type_name, 0),
            }
        )

    suggested_actions = ontology.get("suggested_actions", [])
    suggested_action_counts = count_by(suggested_actions, "actionType")
    action_axioms: list[dict[str, Any]] = []
    for action_name, spec in action_schema.get("actions", {}).items():
        action_axioms.append(
            {
                "action": action_name,
                "zh_name": spec.get("zh_name", ""),
                "group": spec.get("group", ""),
                "actor_roles": spec.get("actor_roles", []),
                "target_type": spec.get("target_type", ""),
                "trigger": spec.get("trigger", ""),
                "used_in_v4_suggestions": action_name in suggested_action_counts,
                "suggested_count": suggested_action_counts.get(action_name, 0),
            }
        )

    axiom_catalog = {
        "source_of_truth": {
            "objects": str((args.core_schema_dir / "objects.yaml").resolve()),
            "relations": str((args.core_schema_dir / "relations.yaml").resolve()),
            "actions": str((args.core_schema_dir / "actions.yaml").resolve()),
        },
        "schema_versions": {
            "objects": object_schema.get("schema_version", ""),
            "relations": relation_schema.get("schema_version", ""),
            "actions": action_schema.get("schema_version", ""),
        },
        "interpretation": "公理层来自核心 schema；v4 只实例化这些类型，不在输出中定义新的公理类型。",
        "object_categories": object_schema.get("object_categories", {}),
        "object_types": object_axioms,
        "relation_groups": relation_schema.get("relation_groups", {}),
        "relation_types": relation_axioms,
        "action_groups": action_schema.get("action_groups", {}),
        "actions": action_axioms,
    }

    state_variables = [obj for obj in objects if obj.get("type") == "StateVariable"]
    propagations = [obj for obj in objects if obj.get("type") == "StateVariablePropagation"]
    industry_targets = [
        obj
        for obj in objects
        if obj.get("type") in RESEARCH_TARGET_TYPES
        and obj.get("governanceLayer") == "industry_extension"
    ]
    state_variable_templates = [
        obj
        for obj in state_variables
        if obj.get("fields", {}).get("sourceType") == "industry_template"
        or obj.get("governanceLayer") == "industry_extension"
    ]
    propagation_summaries = {
        item.get("objectId", ""): item for item in ontology.get("propagation_templates", [])
    }

    template_variables: list[dict[str, Any]] = []
    for obj in state_variable_templates:
        observed_on = targets(obj["id"], "observedOn")
        template_variables.append(
            {
                "id": obj["id"],
                "name": obj.get("fields", {}).get("name", ""),
                "category": obj.get("fields", {}).get("category", ""),
                "variable_type": obj.get("fields", {}).get("variableType", ""),
                "description": obj.get("fields", {}).get("description", ""),
                "frequency": obj.get("fields", {}).get("observationFrequency", ""),
                "source_type": obj.get("fields", {}).get("sourceType", ""),
                "governance_layer": obj.get("governanceLayer", ""),
                "record_status": obj.get("recordStatus", ""),
                "evidence_level": obj.get("evidenceLevel", ""),
                "observed_on": [
                    {"id": anchor["id"], "type": anchor["type"], "label": object_label(anchor)}
                    for anchor in observed_on
                ],
            }
        )

    template_propagations: list[dict[str, Any]] = []
    for obj in propagations:
        summary = propagation_summaries.get(obj["id"], {})
        source_variables = targets(obj["id"], "propagatesFrom")
        target_variables = targets(obj["id"], "propagatesTo")
        template_propagations.append(
            {
                "id": obj["id"],
                "logic": obj.get("fields", {}).get("propagationLogic", ""),
                "direction_mapping": obj.get("fields", {}).get("directionMapping", ""),
                "lag_description": obj.get("fields", {}).get("lagDescription", ""),
                "boundary_conditions": obj.get("fields", {}).get("boundaryConditions", ""),
                "causal_confidence": obj.get("fields", {}).get("causalConfidence", ""),
                "historical_support": obj.get("fields", {}).get("historicalSupport", ""),
                "source_variables": [
                    {"id": item["id"], "label": object_label(item)} for item in source_variables
                ],
                "target_variables": [
                    {"id": item["id"], "label": object_label(item)} for item in target_variables
                ],
                "record_status": obj.get("recordStatus", ""),
                "evidence_level": obj.get("evidenceLevel", ""),
                "verified_steps": summary.get("verified_steps", []),
                "missing_steps": summary.get("missing_steps", []),
            }
        )

    industry_template_catalog = {
        "interpretation": {
            "industry_directory": "industry_extension 中的研究标的对象，用于描述半导体行业目录。",
            "state_variable_templates": "sourceType=industry_template 或位于 industry_extension 的状态变量。",
            "propagation_templates": "StateVariablePropagation 对象及其 propagatesFrom/propagatesTo 端点。",
            "caution": "该分类是阅读视图；原始 objects 和 relations 仍是唯一事实源。",
        },
        "industry_directory": [
            {
                "id": obj["id"],
                "type": obj["type"],
                "label": object_label(obj),
                "record_status": obj.get("recordStatus", ""),
                "evidence_level": obj.get("evidenceLevel", ""),
                "anchors": anchors(obj["id"]),
            }
            for obj in industry_targets
        ],
        "state_variable_templates": template_variables,
        "propagation_templates": template_propagations,
    }

    summary_by_type: dict[str, dict[str, dict[str, Any]]] = {}
    for summary_key, type_name in SUMMARY_VIEW_TYPES.items():
        summary_by_type[type_name] = {
            item.get("objectId", ""): item for item in ontology.get(summary_key, [])
        }

    observation_variable_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for relation in relations:
        if relation.get("type") == "observationBindsVariable":
            target = objects_by_id.get(relation.get("targetId", ""))
            if target:
                observation_variable_map[relation.get("sourceId", "")].append(target)
    for item in ontology.get("state_observations", []):
        variable_id = item.get("variableId", "")
        variable = objects_by_id.get(variable_id)
        if variable and variable not in observation_variable_map[item.get("objectId", "")]:
            observation_variable_map[item.get("objectId", "")].append(variable)

    instance_entries: list[dict[str, Any]] = []
    for obj in objects:
        fields = obj.get("fields", {})
        if obj.get("type") == "StateVariable" and (
            fields.get("sourceType") == "industry_template"
            or obj.get("governanceLayer") == "industry_extension"
        ):
            reading_role = "template_definition"
        elif obj.get("type") == "StateVariablePropagation":
            reading_role = "template_definition"
        elif obj.get("type") in RESEARCH_TARGET_TYPES:
            reading_role = "research_target_instance"
        elif obj.get("type") == "StateVariableObservation":
            reading_role = "fact_observation"
        else:
            reading_role = "reasoning_instance"
        instance_entries.append(
            {
                "id": obj["id"],
                "type": obj.get("type", ""),
                "label": object_label(obj),
                "reading_role": reading_role,
                "governance_layer": obj.get("governanceLayer", ""),
                "record_status": obj.get("recordStatus", ""),
                "evidence_level": obj.get("evidenceLevel", ""),
                "extraction_confidence": obj.get("extractionConfidence"),
                "anchors": anchors(obj["id"]),
                "bound_variables": [
                    {"id": item["id"], "label": object_label(item)}
                    for item in observation_variable_map.get(obj["id"], [])
                ],
            }
        )

    instance_catalog = {
        "interpretation": "实例层目录覆盖所有 objects；reading_role 只是为了阅读，不改变原始对象类型。",
        "counts": {
            "by_type": object_counts,
            "by_governance_layer": governance_counts,
            "by_record_status": object_status_counts,
            "by_reading_role": dict(
                sorted(Counter(item["reading_role"] for item in instance_entries).items())
            ),
        },
        "instances": instance_entries,
    }

    reasoning_views: list[dict[str, Any]] = []
    judgments = [obj for obj in objects if obj.get("type") == "JudgmentOutput"]
    for judgment in judgments:
        hypotheses = targets(judgment["id"], "basedOnHypothesis")
        judgment_events = targets(judgment["id"], "basedOnEvent")
        hypothesis_views = []
        all_events = {item["id"]: item for item in judgment_events}
        for hypothesis in hypotheses:
            bound_variables = targets(hypothesis["id"], "hypothesisBindsVariable")
            hypothesis_events = targets(hypothesis["id"], "basedOnEvent")
            all_events.update({item["id"]: item for item in hypothesis_events})
            signal_links = []
            for relation_type, role_label in SIGNAL_RELATION_ROLES.items():
                for signal in sources(hypothesis["id"], relation_type):
                    signal_links.append(
                        {
                            "role": role_label,
                            "relation_type": relation_type,
                            "id": signal["id"],
                            "label": object_label(signal),
                        }
                    )
            hypothesis_views.append(
                {
                    "id": hypothesis["id"],
                    "label": object_label(hypothesis),
                    "bound_variables": [
                        {"id": item["id"], "label": object_label(item)}
                        for item in bound_variables
                    ],
                    "events": [
                        {"id": item["id"], "label": object_label(item)}
                        for item in hypothesis_events
                    ],
                    "signals": signal_links,
                }
            )
        impacts = sources(judgment["id"], "impactDerivedFrom")
        impact_views = []
        for impact in impacts:
            assets = targets(impact["id"], "impactsAsset")
            impact_views.append(
                {
                    "id": impact["id"],
                    "label": object_label(impact),
                    "impact_direction": impact.get("fields", {}).get("impactDirection", ""),
                    "impact_magnitude": impact.get("fields", {}).get("impactMagnitude", ""),
                    "assets": [
                        {"id": item["id"], "label": object_label(item)} for item in assets
                    ],
                }
            )
        reasoning_views.append(
            {
                "judgment_id": judgment["id"],
                "judgment": object_label(judgment),
                "record_status": judgment.get("recordStatus", ""),
                "evidence_level": judgment.get("evidenceLevel", ""),
                "events": [
                    {"id": item["id"], "label": object_label(item)}
                    for item in all_events.values()
                ],
                "hypotheses": hypothesis_views,
                "asset_impacts": impact_views,
            }
        )

    linked_hypothesis_ids = {
        hypothesis["id"]
        for view in reasoning_views
        for hypothesis in view.get("hypotheses", [])
    }
    linked_impact_ids = {
        impact["id"]
        for view in reasoning_views
        for impact in view.get("asset_impacts", [])
    }
    all_hypothesis_ids = {
        obj["id"] for obj in objects if obj.get("type") == "StateHypothesis"
    }
    all_impact_ids = {obj["id"] for obj in objects if obj.get("type") == "AssetImpact"}
    reasoning_catalog = {
        "interpretation": "以 JudgmentOutput 为中心，把事件、假设、变量、信号、资产影响和资产拼成局部推理链。",
        "propagation_templates": template_propagations,
        "judgment_views": reasoning_views,
        "coverage": {
            "judgments": len(judgments),
            "linked_hypotheses": len(linked_hypothesis_ids),
            "unlinked_hypotheses": sorted(all_hypothesis_ids - linked_hypothesis_ids),
            "linked_asset_impacts": len(linked_impact_ids),
            "unlinked_asset_impacts": sorted(all_impact_ids - linked_impact_ids),
        },
    }

    summary_view_consistency: list[dict[str, Any]] = []
    for summary_key, type_name in SUMMARY_VIEW_TYPES.items():
        object_ids = {obj["id"] for obj in objects if obj.get("type") == type_name}
        summary_ids = {
            item.get("objectId", "") for item in ontology.get(summary_key, []) if item.get("objectId")
        }
        summary_view_consistency.append(
            {
                "summary_view": summary_key,
                "object_type": type_name,
                "object_count": len(object_ids),
                "summary_count": len(summary_ids),
                "missing_from_summary": sorted(object_ids - summary_ids),
                "extra_in_summary": sorted(summary_ids - object_ids),
                "consistent": object_ids == summary_ids,
            }
        )

    observation_objects = [
        obj for obj in objects if obj.get("type") == "StateVariableObservation"
    ]
    unbound_observations = [
        obj["id"] for obj in observation_objects if not observation_variable_map.get(obj["id"])
    ]
    template_layer_mismatch = [
        item["id"]
        for item in template_variables
        if item["source_type"] == "industry_template"
        and item["governance_layer"] != "industry_extension"
    ]
    confirmed_objects = [
        obj["id"] for obj in objects if obj.get("recordStatus") == "confirmed"
    ]
    confirmed_relations = [
        relation["id"] for relation in relations if relation.get("recordStatus") == "confirmed"
    ]

    source_documents = ontology.get("source_documents", [])
    evidence_claims = ontology.get("evidence_claims", [])
    graph_bridge_counts = {
        "source_documents_array": len(source_documents),
        "source_document_objects": object_counts.get("SourceDocument", 0),
        "source_of_relations": relation_counts.get("sourceOf", 0),
        "event_objects": object_counts.get("Event", 0),
        "anchored_on_relations": relation_counts.get("anchoredOn", 0),
        "signal_objects": object_counts.get("Signal", 0),
        "signal_based_on_observation_relations": relation_counts.get(
            "signalBasedOnObservation", 0
        ),
    }
    governance_summary = {
        "source_documents": {
            "count": len(source_documents),
            "by_reliability": count_by(source_documents, "sourceReliability"),
            "by_adoption_status": count_by(source_documents, "adoptionStatus"),
        },
        "evidence_claims": {
            "count": len(evidence_claims),
            "by_statement_type": count_by(evidence_claims, "statement_type"),
            "by_evidence_level": count_by(evidence_claims, "evidence_level"),
        },
        "object_governance": {
            "by_layer": governance_counts,
            "by_status": object_status_counts,
            "by_evidence_level": object_evidence_counts,
            "confirmed_object_ids": confirmed_objects,
        },
        "relation_governance": {
            "by_status": relation_status_counts,
            "by_evidence_level": relation_evidence_counts,
            "confirmed_relation_ids": confirmed_relations,
        },
        "summary_view_consistency": summary_view_consistency,
        "unbound_observations": unbound_observations,
        "industry_template_governance_layer_mismatch": template_layer_mismatch,
        "graph_bridge_counts": graph_bridge_counts,
        "unresolved_objects": ontology.get("unresolved_objects", []),
        "unresolved_relations": ontology.get("unresolved_relations", []),
        "missing_evidence": ontology.get("missing_evidence", []),
        "human_review_required": ontology.get("human_review_required", []),
    }

    metadata = ontology.get("ontology_metadata", {})
    reading_order = [
        "00_阅读入口.md",
        "01_公理层目录.md",
        "02_行业模板层.md",
        "03_实例层目录.md",
        "04_关键推理链.md",
        "05_证据与治理摘要.md",
    ]
    if curated_template_view_exists:
        reading_order.insert(2, "02A_行业模板总览图.md")

    manifest = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_file": str(args.input_json.resolve()),
        "ontology_id": metadata.get("ontology_id", ""),
        "ontology_version": metadata.get("ontology_version", ""),
        "parent_version": metadata.get("parent_version", ""),
        "research_question": ontology.get("industry_context", {}).get("research_question", ""),
        "ontology_quality": metadata.get("ontology_quality", {}),
        "counts": {
            "objects": len(objects),
            "relations": len(relations),
            "source_documents": len(source_documents),
            "evidence_claims": len(evidence_claims),
            "object_types_used": len(object_counts),
            "relation_types_used": len(relation_counts),
            "state_variable_templates": len(template_variables),
            "propagation_templates": len(template_propagations),
            "judgment_views": len(reasoning_views),
        },
        "reading_order": reading_order,
        "machine_readable_views": [
            "manifest.json",
            "axiom_catalog.json",
            "industry_template_catalog.json",
            "instance_catalog.json",
            "reasoning_views.json",
            "governance_summary.json",
        ],
        "authority_rule": "解析目录均为派生视图；原始 optimized_ontology.objects 与 optimized_ontology.relations 是权威实例图，核心 schema 是权威公理层。",
    }

    write_json(output_dir / "manifest.json", manifest)
    write_json(output_dir / "axiom_catalog.json", axiom_catalog)
    write_json(output_dir / "industry_template_catalog.json", industry_template_catalog)
    write_json(output_dir / "instance_catalog.json", instance_catalog)
    write_json(output_dir / "reasoning_views.json", reasoning_catalog)
    write_json(output_dir / "governance_summary.json", governance_summary)

    object_type_total = len(object_axioms)
    relation_type_total = len(relation_axioms)
    all_candidate = object_status_counts == {"candidate": len(objects)}
    inconsistent_summaries = [
        item for item in summary_view_consistency if not item["consistent"]
    ]

    entry_reading_order = [
        "1. `01_公理层目录.md`：先看系统允许有哪些对象类型、关系类型和动作。",
    ]
    if curated_template_view_exists:
        entry_reading_order.append(
            "2. `02A_行业模板总览图.md`：阅读严格由 v4 原始对象、关系和字段生成的行业模板视图。"
        )
        entry_reading_order.extend(
            [
                "3. `02_行业模板层.md`：再下钻查看完整状态变量与传导模板机器明细。",
                "4. `03_实例层目录.md`：然后看具体公司、产品、材料、事件、观测和研究判断。",
                "5. `04_关键推理链.md`：按判断输出下钻到假设、信号和资产影响。",
                "6. `05_证据与治理摘要.md`：最后确认候选状态、证据缺口和一致性问题。",
            ]
        )
    else:
        entry_reading_order.extend(
            [
                "2. `02_行业模板层.md`：查看状态变量与传导模板机器明细。",
                "3. `03_实例层目录.md`：然后看具体公司、产品、材料、事件、观测和研究判断。",
                "4. `04_关键推理链.md`：按判断输出下钻到假设、信号和资产影响。",
                "5. `05_证据与治理摘要.md`：最后确认候选状态、证据缺口和一致性问题。",
            ]
        )

    entry_lines = [
        f"# {ontology.get('industry_context', {}).get('primary_industry', metadata.get('ontology_id', '本体'))} {metadata.get('ontology_version', '')} 阅读入口",
        "",
        f"- 原始文件：`{args.input_json.name}`",
        f"- 本体版本：`{metadata.get('ontology_version', '')}`",
        f"- 研究问题：{ontology.get('industry_context', {}).get('research_question', '')}",
        f"- 权威规则：核心 schema 定义公理层；原始 `objects` 与 `relations` 定义实例图；本目录均为派生阅读视图。",
        "",
        "## 建议阅读顺序",
        "",
        *entry_reading_order,
        "",
        "## 规模概览",
        "",
        table(
            ["项目", "数量"],
            [
                ["对象实例", len(objects)],
                ["关系实例", len(relations)],
                ["使用的对象类型", f"{len(object_counts)} / {object_type_total}"],
                ["使用的关系类型", f"{len(relation_counts)} / {relation_type_total}"],
                ["行业状态变量模板", len(template_variables)],
                ["行业传导模板", len(template_propagations)],
                ["来源材料", len(source_documents)],
                ["证据主张", len(evidence_claims)],
                ["判断中心推理视图", len(reasoning_views)],
            ],
        ),
        "",
        "## 一眼结论",
        "",
        f"- `v4` 没有自行定义新的公理类型，而是使用核心规范中的 {len(object_counts)} 种对象类型和 {len(relation_counts)} 种关系类型。",
        f"- 按固定阅读顺序，先看 {len(template_variables)} 个状态变量模板和 {len(template_propagations)} 条传导模板，再下钻全部 {len(objects)} 个对象实例。",
        f"- 对象治理层分布：{md(governance_counts)}。",
        f"- 对象状态分布：{md(object_status_counts)}。",
    ]
    if all_candidate:
        entry_lines.append(
        "- 所有对象实例目前都是 `candidate`，因此这是一份候选本体，不应被当作已确认知识库。"
        )
    if inconsistent_summaries:
        entry_lines.append(
            f"- 有 {len(inconsistent_summaries)} 个摘要数组与权威 `objects` 数量或 ID 不一致，详见 `05_证据与治理摘要.md`。"
        )
    if unbound_observations:
        entry_lines.append(
            f"- 有 {len(unbound_observations)} 个观测对象未通过关系或摘要视图绑定状态变量，AI 推理时应谨慎使用。"
        )
    entry_lines.extend(
        [
            "",
            "## 质量分数",
            "",
            table(
                ["维度", "分数"],
                [
                    [key, value]
                    for key, value in metadata.get("ontology_quality", {}).items()
                ],
            ),
        ]
    )
    write_text(output_dir / "00_阅读入口.md", "\n".join(entry_lines))

    category_specs = object_schema.get("object_categories", {})
    object_rows = []
    for item in object_axioms:
        category = category_specs.get(item["category"], {}).get("zh_name", item["category"])
        object_rows.append(
            [
                item["type"],
                item["zh_name"],
                category,
                item["instance_count"],
                "是" if item["used_in_v4"] else "否",
                item["description"],
            ]
        )
    relation_rows = []
    for item in relation_axioms:
        group = relation_schema.get("relation_groups", {}).get(item["group"], {}).get(
            "zh_name", item["group"]
        )
        relation_rows.append(
            [
                item["type"],
                item["zh_name"],
                group,
                list_or_none(item["source_types"]),
                list_or_none(item["target_types"]),
                item["instance_count"],
                "是" if item["used_in_v4"] else "否",
            ]
        )
    used_action_rows = [
        [
            item["action"],
            item["zh_name"],
            item["group"],
            list_or_none(item["actor_roles"]),
            item["target_type"],
            item["suggested_count"],
        ]
        for item in action_axioms
        if item["used_in_v4_suggestions"]
    ]
    axiom_md = "\n".join(
        [
            "# 公理层目录",
            "",
            "公理层不是 `v4` 长 JSON 中的具体公司和事件，而是核心 schema 规定的对象类型、关系类型、动作和约束。`v4` 只是这些公理类型的一组候选实例。",
            "",
            f"- 对象公理来源：`{args.core_schema_dir / 'objects.yaml'}`",
            f"- 关系公理来源：`{args.core_schema_dir / 'relations.yaml'}`",
            f"- 动作公理来源：`{args.core_schema_dir / 'actions.yaml'}`",
            "",
            "## 对象类型",
            "",
            table(
                ["类型", "中文名", "类别", "v4实例数", "v4使用", "含义"],
                object_rows,
            ),
            "",
            "## 关系类型",
            "",
            table(
                ["关系", "中文名", "关系组", "源类型", "目标类型", "v4实例数", "v4使用"],
                relation_rows,
            ),
            "",
            "## v4 建议动作涉及的动作类型",
            "",
            table(
                ["动作", "中文名", "动作组", "角色", "目标类型", "建议数"],
                used_action_rows,
            ),
            "",
            "## 阅读提示",
            "",
            "- `Industry`、`Company`、`Product` 等是实体类型，不是具体实体。",
            "- `companyBelongsToIndustry`、`supportsHypothesis` 等是关系公理，不是某一条具体关系。",
            "- 半导体行业特有的变量和传导规律不属于核心公理层，应在行业模板层阅读。",
        ]
    )
    write_text(output_dir / "01_公理层目录.md", axiom_md)

    segment_directory_rows = []
    for obj in objects:
        if obj.get("type") != "Segment":
            continue
        parent_industries = targets(obj["id"], "segmentBelongsToIndustry")
        segment_directory_rows.append(
            [
                obj["id"],
                object_label(obj),
                list_or_none(
                    f"{industry['id']} {object_label(industry)}"
                    for industry in parent_industries
                ),
                obj.get("governanceLayer", ""),
                obj.get("recordStatus", ""),
                obj.get("evidenceLevel", ""),
            ]
        )

    propagation_diagram_lines = []
    sorted_propagations = sorted(template_propagations, key=lambda item: item["id"])
    for index in range(0, len(sorted_propagations), 6):
        chunk = sorted_propagations[index : index + 6]
        propagation_diagram_lines.extend(
            [
                "",
                f"### 传导模板关系图 {index // 6 + 1}",
                "",
                "```mermaid",
                "flowchart LR",
            ]
        )
        defined_nodes: set[str] = set()
        for item in chunk:
            for source_variable in item["source_variables"]:
                source_node = mermaid_id(source_variable["id"])
                if source_node not in defined_nodes:
                    propagation_diagram_lines.append(
                        f'  {source_node}["{mermaid_label(source_variable["id"] + " " + source_variable["label"])}"]'
                    )
                    defined_nodes.add(source_node)
                for target_variable in item["target_variables"]:
                    target_node = mermaid_id(target_variable["id"])
                    if target_node not in defined_nodes:
                        propagation_diagram_lines.append(
                            f'  {target_node}["{mermaid_label(target_variable["id"] + " " + target_variable["label"])}"]'
                        )
                        defined_nodes.add(target_node)
                    propagation_diagram_lines.append(
                        f'  {source_node} -->|"{mermaid_label(item["id"])}"| {target_node}'
                    )
        propagation_diagram_lines.append("```")

    faithful_propagation_rows = [
        [
            item["id"],
            list_or_none(
                f"{source['id']} {source['label']}" for source in item["source_variables"]
            ),
            list_or_none(
                f"{target['id']} {target['label']}" for target in item["target_variables"]
            ),
            item["logic"],
            item["lag_description"],
            item["boundary_conditions"],
            item["evidence_level"],
            item["causal_confidence"],
        ]
        for item in sorted_propagations
    ]

    variables_by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in template_variables:
        variables_by_category[item["category"]].append(item)
    variable_category_lines = []
    for category, items in sorted(variables_by_category.items()):
        variable_category_lines.extend(
            [
                "",
                f"### {category}",
                "",
                table(
                    ["ID", "变量名称", "变量类型", "观察频率", "挂载对象", "证据等级"],
                    [
                        [
                            item["id"],
                            item["name"],
                            item["variable_type"],
                            item["frequency"],
                            list_or_none(
                                f"{anchor['id']} {anchor['label']}"
                                for anchor in item["observed_on"]
                            ),
                            item["evidence_level"],
                        ]
                        for item in items
                    ],
                ),
            ]
        )

    faithful_template_md_lines = [
        "# 行业模板层可追溯阅读视图",
        "",
        "本文件只重排 `v4` 原始本体中已经存在的内容，不新增对象、变量、关系、传导步骤或行业判断。",
        "",
        "- 节点名称来自 `optimized_ontology.objects`。",
        "- 关系图中的连线来自 `optimized_ontology.relations`。",
        "- 传导逻辑、滞后、边界条件来自 `StateVariablePropagation.fields`。",
        "- 变量分组来自 `StateVariable.fields.category`。",
        "",
        "## 一、行业环节目录",
        "",
        "以下目录只列出 `v4` 中类型为 `Segment` 的对象，以及它们已有的 `segmentBelongsToIndustry` 关系。",
        "",
        table(
            ["Segment ID", "名称", "所属 Industry", "治理层", "状态", "证据等级"],
            segment_directory_rows,
        ),
        "",
        "## 二、传导模板关系图",
        "",
        "下面是人类阅读投影：将同一 `StateVariablePropagation` 对象已有的 `propagatesFrom` 和 `propagatesTo` 端点合并显示为“源变量 → 目标变量”，箭头标注模板 ID。它不新增正式关系。为避免画面拥挤，16 条模板按 ID 顺序拆成三张图。",
        *propagation_diagram_lines,
        "",
        "## 三、传导模板原文对照",
        "",
        table(
            [
                "模板 ID",
                "propagatesFrom",
                "propagatesTo",
                "propagationLogic",
                "lagDescription",
                "boundaryConditions",
                "证据等级",
                "因果置信度",
            ],
            faithful_propagation_rows,
        ),
        "",
        "## 四、状态变量目录",
        "",
        "以下状态变量仅按其原始 `category` 字段分组。公司级变量、行业级变量和其他变量保持原样，不在本阅读视图中重新分类。",
        *variable_category_lines,
        "",
        "## 五、阅读边界",
        "",
        "- 本文件帮助理解 `v4` 已经表达了什么，不判断这些模板是否正确。",
        "- 如果关系图与传导逻辑文字看起来不一致，应回到原始对象和关系检查，而不是在阅读视图中补充新节点。",
        "- 原始 `optimized_ontology.objects` 与 `optimized_ontology.relations` 仍是权威实例图。",
    ]
    write_text(output_dir / "02A_行业模板总览图.md", "\n".join(faithful_template_md_lines))

    target_rows = [
        [
            item["type"],
            item["id"],
            item["label"],
            item["record_status"],
            item["evidence_level"],
        ]
        for item in industry_template_catalog["industry_directory"]
    ]
    variable_rows = [
        [
            item["category"],
            item["id"],
            item["name"],
            item["variable_type"],
            item["frequency"],
            list_or_none(anchor["label"] for anchor in item["observed_on"]),
            item["evidence_level"],
        ]
        for item in template_variables
    ]
    propagation_rows = [
        [
            item["id"],
            list_or_none(source["label"] for source in item["source_variables"]),
            list_or_none(target["label"] for target in item["target_variables"]),
            shorten(item["logic"], 150),
            item["evidence_level"],
            item["causal_confidence"],
        ]
        for item in template_propagations
    ]
    template_md_lines = [
        "# 行业模板层机器明细",
        "",
        "本文件是状态变量与传导模板的完整机器明细目录，不建议作为人的第一阅读入口。",
        "",
        "请先阅读 `02A_行业模板总览图.md`。该文件严格重排 v4 原始对象、关系和字段，再使用本文件下钻到完整变量和模板明细。",
        "",
        "## 行业目录骨架",
        "",
        table(["类型", "ID", "名称", "状态", "证据等级"], target_rows),
        "",
        "## 状态变量模板",
        "",
        table(
            ["分类", "ID", "变量", "类型", "观察频率", "挂载对象", "证据等级"],
            variable_rows,
        ),
        "",
        "## 传导模板",
        "",
        table(
            ["ID", "源变量", "目标变量", "传导逻辑", "证据等级", "因果置信度"],
            propagation_rows,
        ),
        "",
        "## 模板层治理提示",
        "",
        f"- 共识别 {len(template_variables)} 个状态变量模板、{len(template_propagations)} 条传导模板。",
        f"- 有 {len(template_layer_mismatch)} 个 `sourceType=industry_template` 的变量不在 `industry_extension` 治理层：{list_or_none(template_layer_mismatch)}。",
        "- 公司级变量也被标记为 `industry_template` 时，应确认它们是可复用模板，还是只属于当前实例研究。",
        "- 传导模板均为候选规则，必须结合边界条件、滞后、观测事实和反证信号使用。",
    ]
    write_text(output_dir / "02_行业模板层.md", "\n".join(template_md_lines))

    instance_md_lines = [
        "# 实例层目录",
        "",
        "实例层回答“当前本体里具体有什么”。本目录列出真实世界实体、事实观测和研究推理实例；模板定义请到 `02_行业模板层.md` 阅读。",
        "",
        "## 实例计数",
        "",
        table(
            ["对象类型", "数量"],
            [[type_name, count] for type_name, count in object_counts.items()],
        ),
    ]
    for type_name in RESEARCH_TARGET_TYPES:
        type_objects = [obj for obj in objects if obj.get("type") == type_name]
        if not type_objects:
            continue
        instance_md_lines.extend(
            [
                "",
                f"## {type_name}",
                "",
                table(
                    ["ID", "名称", "治理层", "状态", "证据等级"],
                    [
                        [
                            obj["id"],
                            object_label(obj),
                            obj.get("governanceLayer", ""),
                            obj.get("recordStatus", ""),
                            obj.get("evidenceLevel", ""),
                        ]
                        for obj in type_objects
                    ],
                ),
            ]
        )

    observation_rows = []
    for obj in observation_objects:
        fields = obj.get("fields", {})
        bound = observation_variable_map.get(obj["id"], [])
        observation_rows.append(
            [
                obj["id"],
                list_or_none(object_label(item) for item in bound),
                fields.get("observationTime", ""),
                shorten(fields.get("observedValue", ""), 160),
                obj.get("evidenceLevel", ""),
            ]
        )
    instance_md_lines.extend(
        [
            "",
            "## StateVariableObservation",
            "",
            table(["ID", "绑定变量", "时间", "观测值", "证据等级"], observation_rows),
        ]
    )
    for type_name in REASONING_INSTANCE_TYPES:
        type_objects = [obj for obj in objects if obj.get("type") == type_name]
        if not type_objects:
            continue
        instance_md_lines.extend(
            [
                "",
                f"## {type_name}",
                "",
                table(
                    ["ID", "名称或摘要", "状态", "证据等级"],
                    [
                        [
                            obj["id"],
                            object_label(obj),
                            obj.get("recordStatus", ""),
                            obj.get("evidenceLevel", ""),
                        ]
                        for obj in type_objects
                    ],
                ),
            ]
        )
    write_text(output_dir / "03_实例层目录.md", "\n".join(instance_md_lines))

    reasoning_md_lines = [
        "# 关键推理链",
        "",
        "本文件以判断输出为中心，把局部子图展开为“事件 / 变量 / 假设 / 信号 / 判断 / 资产影响 / 资产”。这比直接阅读全部关系数组更适合人工复核。",
        "",
        "```mermaid",
        "flowchart LR",
        '  E["事件或观测"] --> H["状态假设"]',
        '  V["状态变量"] --> H',
        '  S["支持 / 跟踪 / 削弱 / 阻断信号"] --> H',
        '  H --> J["判断输出"]',
        '  J --> I["资产影响"]',
        '  I --> A["资产"]',
        "```",
        "",
        "## 变量传导链",
        "",
        table(
            ["ID", "源变量", "目标变量", "传导逻辑", "缺失步骤"],
            [
                [
                    item["id"],
                    list_or_none(source["label"] for source in item["source_variables"]),
                    list_or_none(target["label"] for target in item["target_variables"]),
                    shorten(item["logic"], 160),
                    list_or_none(item["missing_steps"]),
                ]
                for item in template_propagations
            ],
        ),
        "",
        "## 判断中心子图",
    ]
    for view in reasoning_views:
        reasoning_md_lines.extend(
            [
                "",
                f"### {view['judgment_id']} {view['judgment']}",
                "",
                f"- 状态：`{view['record_status']}`；证据等级：`{view['evidence_level']}`。",
                "- 事件："
                + list_or_none(
                    f"{item['id']} {item['label']}" for item in view["events"]
                )
                + "。",
            ]
        )
        if view["hypotheses"]:
            reasoning_md_lines.append("- 假设与信号：")
            for hypothesis in view["hypotheses"]:
                variable_text = list_or_none(
                    f"{item['id']} {item['label']}" for item in hypothesis["bound_variables"]
                )
                signal_text = list_or_none(
                    f"{item['role']}:{item['id']} {item['label']}"
                    for item in hypothesis["signals"]
                )
                reasoning_md_lines.append(
                    f"  - `{hypothesis['id']}` {hypothesis['label']}；绑定变量：{variable_text}；信号：{signal_text}。"
                )
        else:
            reasoning_md_lines.append("- 假设：无显式 `basedOnHypothesis` 关系。")
        if view["asset_impacts"]:
            reasoning_md_lines.append("- 资产影响：")
            for impact in view["asset_impacts"]:
                assets_text = list_or_none(
                    f"{item['id']} {item['label']}" for item in impact["assets"]
                )
                reasoning_md_lines.append(
                    f"  - `{impact['id']}` 方向 `{impact['impact_direction']}`、幅度 `{impact['impact_magnitude']}`；资产：{assets_text}。"
                )
        else:
            reasoning_md_lines.append("- 资产影响：无显式 `impactDerivedFrom` 关系。")
    reasoning_md_lines.extend(
        [
            "",
            "## 链路覆盖提示",
            "",
            f"- 未连接到判断输出的假设：{list_or_none(reasoning_catalog['coverage']['unlinked_hypotheses'])}。",
            f"- 未连接到判断输出的资产影响：{list_or_none(reasoning_catalog['coverage']['unlinked_asset_impacts'])}。",
        ]
    )
    write_text(output_dir / "04_关键推理链.md", "\n".join(reasoning_md_lines))

    consistency_rows = [
        [
            item["summary_view"],
            item["object_type"],
            item["object_count"],
            item["summary_count"],
            "一致" if item["consistent"] else "不一致",
            list_or_none(item["missing_from_summary"]),
            list_or_none(item["extra_in_summary"]),
        ]
        for item in summary_view_consistency
    ]
    missing_rows = [
        [
            item.get("gap", ""),
            item.get("why_it_matters", ""),
            item.get("suggested_material", ""),
        ]
        for item in ontology.get("missing_evidence", [])
    ]
    review_rows = [
        [
            item.get("item", ""),
            item.get("reason", ""),
            item.get("suggested_reviewer_role", ""),
        ]
        for item in ontology.get("human_review_required", [])
    ]
    governance_md_lines = [
        "# 证据与治理摘要",
        "",
        "这一层只复述 `v4` 原始本体中的治理状态、证据等级、缺失证据和人工审核项。",
        "",
        "## 状态概览",
        "",
        table(
            ["项目", "分布"],
            [
                ["对象治理层", governance_counts],
                ["对象记录状态", object_status_counts],
                ["对象证据等级", object_evidence_counts],
                ["关系记录状态", relation_status_counts],
                ["关系证据等级", relation_evidence_counts],
                ["来源可靠性", governance_summary["source_documents"]["by_reliability"]],
                ["证据主张类型", governance_summary["evidence_claims"]["by_statement_type"]],
            ],
        ),
        "",
        "## 摘要视图一致性",
        "",
        "以下数组应被视为 `objects` 的派生阅读视图。如果 ID 集合不一致，AI 推理应优先使用 `objects + relations`。",
        "",
        table(
            ["摘要数组", "对象类型", "objects数", "摘要数", "结果", "摘要缺失ID", "摘要额外ID"],
            consistency_rows,
        ),
        "",
        "## 结构性风险",
        "",
        f"- 未绑定状态变量的观测对象：{list_or_none(unbound_observations)}。",
        f"- `industry_template` 与治理层不一致的状态变量：{list_or_none(template_layer_mismatch)}。",
        f"- 已确认对象数：{len(confirmed_objects)}；已确认关系数：{len(confirmed_relations)}。",
        f"- 来源材料数组有 {graph_bridge_counts['source_documents_array']} 项，但 `SourceDocument` 对象有 {graph_bridge_counts['source_document_objects']} 个、`sourceOf` 关系有 {graph_bridge_counts['source_of_relations']} 条；证据目前不能完全通过核心对象图遍历。",
        f"- 事件对象有 {graph_bridge_counts['event_objects']} 个，但 `anchoredOn` 关系有 {graph_bridge_counts['anchored_on_relations']} 条；信号对象有 {graph_bridge_counts['signal_objects']} 个，但 `signalBasedOnObservation` 关系有 {graph_bridge_counts['signal_based_on_observation_relations']} 条。",
        "- 当已确认对象和关系均为零时，本体应被解释为候选知识图谱，不是可直接执行的正式知识库。",
        "",
        "## 缺失证据",
        "",
        table(["缺口", "重要性", "建议材料"], missing_rows),
        "",
        "## 人工审核项",
        "",
        table(["项目", "原因", "建议角色"], review_rows),
    ]
    write_text(output_dir / "05_证据与治理摘要.md", "\n".join(governance_md_lines))

    object_type_names = {
        item["type"]: item["zh_name"] or item["type"] for item in object_axioms
    }
    relation_type_names = {
        item["type"]: item["zh_name"] or item["type"] for item in relation_axioms
    }

    def distribution_text(counts: dict[str, int]) -> str:
        if not counts:
            return "原本体未提供"
        return "、".join(
            f"`{key or '未标记'}` {value}" for key, value in counts.items()
        )

    def object_ref(obj: dict[str, Any] | None, object_id: str = "") -> str:
        if not obj:
            return object_id or "原本体未提供"
        label = object_label(obj)
        return f"{obj.get('id', object_id)} {label}".strip()

    def table_or_none(headers: list[str], rows: Iterable[Iterable[Any]]) -> str:
        materialized = list(rows)
        if not materialized:
            return "原本体未提供。"
        return table(headers, materialized)

    def details_block(summary: str, body: str) -> str:
        return "\n".join(
            [
                "<details>",
                f"<summary>{summary}</summary>",
                "",
                body,
                "",
                "</details>",
            ]
        )

    used_object_type_rows = [
        [
            item["zh_name"] or item["type"],
            f"`{item['type']}`",
            item["instance_count"],
            item["description"],
        ]
        for item in object_axioms
        if item["used_in_v4"]
    ]
    used_relation_type_rows = [
        [
            item["zh_name"] or item["type"],
            f"`{item['type']}`",
            item["instance_count"],
            list_or_none(item["source_types"]),
            list_or_none(item["target_types"]),
        ]
        for item in relation_axioms
        if item["used_in_v4"]
    ]
    all_object_schema_rows = [
        [
            item["zh_name"] or item["type"],
            f"`{item['type']}`",
            item["category"],
            item["instance_count"],
            "是" if item["used_in_v4"] else "否",
            item["description"],
        ]
        for item in object_axioms
    ]
    all_relation_schema_rows = [
        [
            item["zh_name"] or item["type"],
            f"`{item['type']}`",
            item["group"],
            item["instance_count"],
            "是" if item["used_in_v4"] else "否",
            item["description"],
        ]
        for item in relation_axioms
    ]

    def object_rows_for_type(type_name: str) -> list[list[Any]]:
        return [
            [
                obj["id"],
                object_label(obj),
                obj.get("recordStatus", ""),
                obj.get("evidenceLevel", ""),
                obj.get("governanceLayer", ""),
            ]
            for obj in objects
            if obj.get("type") == type_name
        ]

    observation_report_rows = []
    for obj in observation_objects:
        fields = obj.get("fields", {})
        bound = observation_variable_map.get(obj["id"], [])
        observation_report_rows.append(
            [
                obj["id"],
                list_or_none(object_ref(item) for item in bound),
                fields.get("observationTime", ""),
                fields.get("observedValue", ""),
                obj.get("recordStatus", ""),
                obj.get("evidenceLevel", ""),
            ]
        )

    reasoning_instance_rows = []
    for type_name in REASONING_INSTANCE_TYPES:
        for obj in objects:
            if obj.get("type") == type_name:
                reasoning_instance_rows.append(
                    [
                        object_type_names.get(type_name, type_name),
                        obj["id"],
                        object_label(obj),
                        obj.get("recordStatus", ""),
                        obj.get("evidenceLevel", ""),
                    ]
                )

    object_index_rows = [
        [
            obj["id"],
            object_type_names.get(obj.get("type", ""), obj.get("type", "")),
            object_label(obj),
            obj.get("recordStatus", ""),
            obj.get("evidenceLevel", ""),
            obj.get("governanceLayer", ""),
        ]
        for obj in objects
    ]
    relation_index_rows = []
    unresolved_relation_rows = []
    for relation in relations:
        source = objects_by_id.get(relation.get("sourceId", ""))
        target = objects_by_id.get(relation.get("targetId", ""))
        row = [
            relation.get("id", ""),
            relation_type_names.get(relation.get("type", ""), relation.get("type", "")),
            object_ref(source, relation.get("sourceId", "")),
            object_ref(target, relation.get("targetId", "")),
            relation.get("recordStatus", ""),
            relation.get("evidenceLevel", ""),
        ]
        relation_index_rows.append(row)
        if not source or not target:
            unresolved_relation_rows.append(row)

    source_document_rows = [
        [
            item.get("id", ""),
            item.get("title", ""),
            item.get("publisher", ""),
            item.get("publishTime", ""),
            item.get("sourceReliability", ""),
            item.get("adoptionStatus", ""),
        ]
        for item in source_documents
    ]
    evidence_claim_rows = [
        [
            item.get("id", ""),
            item.get("summary", ""),
            item.get("statement_type", ""),
            item.get("evidence_level", ""),
            item.get("ontology_mapping", ""),
        ]
        for item in evidence_claims
    ]

    propagation_reading_rows = [
        [
            item["id"],
            list_or_none(
                f"{source['id']} {source['label']}" for source in item["source_variables"]
            )
            or "原本体未提供",
            list_or_none(
                f"{target['id']} {target['label']}" for target in item["target_variables"]
            )
            or "原本体未提供",
            item["logic"],
            item["lag_description"],
            item["boundary_conditions"],
            item["record_status"],
            item["evidence_level"],
        ]
        for item in sorted_propagations
    ]

    variable_report_rows = [
        [
            item["name"],
            item["id"],
            item["category"],
            item["variable_type"],
            item["frequency"],
            list_or_none(
                f"{anchor['id']} {anchor['label']}" for anchor in item["observed_on"]
            )
            or "原本体未提供挂载对象",
            item["record_status"],
            item["evidence_level"],
        ]
        for item in template_variables
    ]

    industry_topic_rows = []
    for type_name in ["Industry", "Segment", "Product", "Material"]:
        for obj in objects:
            if obj.get("type") == type_name:
                industry_topic_rows.append(
                    [
                        object_type_names.get(type_name, type_name),
                        obj["id"],
                        object_label(obj),
                        obj.get("recordStatus", ""),
                        obj.get("evidenceLevel", ""),
                        obj.get("governanceLayer", ""),
                    ]
                )

    judgment_report_lines = []
    for view in reasoning_views:
        judgment_report_lines.extend(
            [
                "",
                f"### {view['judgment_id']} {view['judgment']}",
                "",
                f"- **判断状态**：`{view['record_status']}`",
                f"- **证据等级**：`{view['evidence_level']}`",
                "- **相关事件**："
                + list_or_none(
                    f"{item['id']} {item['label']}" for item in view["events"]
                ),
            ]
        )
        if view["hypotheses"]:
            for hypothesis in view["hypotheses"]:
                judgment_report_lines.extend(
                    [
                        f"- **相关假设**：`{hypothesis['id']}` {hypothesis['label']}",
                        "- **绑定变量**："
                        + list_or_none(
                            f"{item['id']} {item['label']}"
                            for item in hypothesis["bound_variables"]
                        ),
                        "- **信号**："
                        + list_or_none(
                            f"{item['role']} `({item['relation_type']})`：{item['id']} {item['label']}"
                            for item in hypothesis["signals"]
                        ),
                    ]
                )
        else:
            judgment_report_lines.append("- **相关假设**：原本体未提供显式关系。")
        if view["asset_impacts"]:
            for impact in view["asset_impacts"]:
                judgment_report_lines.append(
                    "- **资产影响**："
                    f"`{impact['id']}` {impact['label']}；"
                    f"方向 `{impact['impact_direction']}`；幅度 `{impact['impact_magnitude']}`；"
                    "资产："
                    + list_or_none(
                        f"{item['id']} {item['label']}" for item in impact["assets"]
                    )
                )
        else:
            judgment_report_lines.append("- **资产影响**：原本体未提供显式关系。")

    ontology_quality_rows = [
        [key, value] for key, value in metadata.get("ontology_quality", {}).items()
    ]
    compact_scope_rows = [
        ["研究主题", ontology.get("industry_context", {}).get("primary_industry", "")],
        ["核心研究问题", ontology.get("industry_context", {}).get("research_question", "")],
        ["业务时间范围", ontology.get("industry_context", {}).get("business_time_range", "")],
        [
            "覆盖范围",
            "、".join(
                [
                    f"行业 {object_counts.get('Industry', 0)}",
                    f"环节 {object_counts.get('Segment', 0)}",
                    f"公司 {object_counts.get('Company', 0)}",
                    f"产品 {object_counts.get('Product', 0)}",
                    f"材料 {object_counts.get('Material', 0)}",
                    f"资产 {object_counts.get('Asset', 0)}",
                ]
            ),
        ],
        ["对象与关系规模", f"对象 {len(objects)}；关系 {len(relations)}"],
        [
            "研究变量规模",
            f"状态变量 {object_counts.get('StateVariable', 0)}；观测 {object_counts.get('StateVariableObservation', 0)}；传导模板 {object_counts.get('StateVariablePropagation', 0)}",
        ],
        [
            "推理实例规模",
            f"事件 {object_counts.get('Event', 0)}；假设 {object_counts.get('StateHypothesis', 0)}；信号 {object_counts.get('Signal', 0)}；判断 {object_counts.get('JudgmentOutput', 0)}；资产影响 {object_counts.get('AssetImpact', 0)}",
        ],
        ["当前记录状态", distribution_text(object_status_counts)],
        ["证据等级分布", distribution_text(object_evidence_counts)],
    ]

    report_lines = [
        "# 投研本体人类可读解析报告",
        "",
        "## 1. 阅读说明",
        "",
        f"本报告用于解释 `{args.input_json.name}` 中已经存在的本体内容，不新增对象、关系、变量、传导步骤或研究结论。",
        "",
        f"> **本体**：{metadata.get('ontology_id', '')} v{metadata.get('ontology_version', '')}",
        f"> **父版本**：{metadata.get('parent_version', '')}",
        "> **本体位置**：`optimized_ontology`",
        "> **权威对象图**：`optimized_ontology.objects`",
        "> **权威关系图**：`optimized_ontology.relations`",
        f"> **解析时间**：{manifest['generated_at']}",
        "",
        "权威规则：`objects + relations` 是权威实例图；`state_variables`、`propagation_templates`、`events`、`signals` 等数组只作为摘要或阅读视图校验。核心 schema 只用于解释类型和字段含义，不向实例层添加内容。",
        "",
        "推荐阅读顺序：先看一页概览，再看类型能力、行业模板、实例层、推理链，最后看证据与治理状态。统计、投影和差异均为可由原 JSON 机械验证的阅读结果。",
        "",
        "## 2. 一页概览",
        "",
        table(["项目", "内容"], compact_scope_rows),
        "",
        "### 报告统计：质量分数",
        "",
        table_or_none(["维度", "原始分数"], ontology_quality_rows),
        "",
        "### 原 JSON 已写明的版本说明",
        "",
        ontology.get("industry_context", {}).get("notes", "原本体未提供。"),
        "",
        "## 3. 这份本体能描述什么",
        "",
        "本章节对应类型能力层。正文只使用研究员可读名称，括号中保留原始类型，便于回到 schema 和 JSON。",
        "",
        "### 当前实际使用的对象类型",
        "",
        table(["研究员名称", "原始类型", "当前实例数", "用途说明"], used_object_type_rows),
        "",
        "### 当前实际使用的关系类型",
        "",
        table(
            ["研究员名称", "原始关系", "当前关系数", "源类型", "目标类型"],
            used_relation_type_rows,
        ),
        "",
        details_block(
            "查看核心 schema 中全部对象类型与 v4 使用情况",
            table(
                ["研究员名称", "原始类型", "类别", "实例数", "v4使用", "说明"],
                all_object_schema_rows,
            ),
        ),
        "",
        details_block(
            "查看核心 schema 中全部关系类型与 v4 使用情况",
            table(
                ["研究员名称", "原始关系", "关系组", "实例数", "v4使用", "说明"],
                all_relation_schema_rows,
            ),
        ),
        "",
        "## 4. 这个行业或主题通常观察什么",
        "",
        "这里的“通常观察”只指原 JSON 已经定义的状态变量和传导模板，不代表报告根据行业常识总结出的框架。",
        "",
        "### 4.1 行业或主题目录",
        "",
        "以下目录只展示原本体已经存在的行业、环节、产品和材料对象。",
        "",
        table(
            ["类型", "原始 ID", "名称", "状态", "证据等级", "治理层"],
            industry_topic_rows,
        ),
        "",
        "### 4.2 状态变量目录",
        "",
        "以下状态变量按原 JSON 中已有字段展示；如果没有挂载对象，显示“原本体未提供挂载对象”。",
        "",
        table(
            ["变量名称", "原始 ID", "分类", "变量类型", "观察频率", "挂载对象", "状态", "证据等级"],
            variable_report_rows,
        ),
        "",
        "### 4.3 传导模板",
        "",
        "以下是阅读投影：将同一 `StateVariablePropagation` 已有的 `propagatesFrom` 和 `propagatesTo` 端点显示为“源变量 → 目标变量”。该投影不代表新增关系。",
        "",
        table(
            ["追溯 ID", "源变量", "目标变量", "原本体传导逻辑", "滞后", "边界条件", "状态", "证据等级"],
            propagation_reading_rows,
        ),
        "",
        "### 4.4 传导关系图",
        "",
        "以下 Mermaid 图只使用原 JSON 已有状态变量、传导模板和关系端点；箭头标签为模板 ID。",
        *propagation_diagram_lines,
        "",
        "## 5. 当前本体具体覆盖了什么",
        "",
        "本章节回答“这份本体具体包含哪些对象和研究记录”。表格中的状态和证据等级均来自原 JSON。",
    ]

    for type_name, section_title in [
        ("Industry", "5.1 行业"),
        ("Segment", "5.2 产业链环节"),
        ("Company", "5.3 公司"),
        ("Product", "5.4 产品"),
        ("Material", "5.5 材料"),
        ("Asset", "5.6 资产"),
    ]:
        report_lines.extend(
            [
                "",
                f"### {section_title}",
                "",
                table_or_none(
                    ["原始 ID", "名称", "状态", "证据等级", "治理层"],
                    object_rows_for_type(type_name),
                ),
            ]
        )

    report_lines.extend(
        [
            "",
            "### 5.7 事实观测",
            "",
            table(
                ["原始 ID", "绑定状态变量", "观测时间", "观测值", "状态", "证据等级"],
                observation_report_rows,
            ),
            "",
            "### 5.8 事件、假设、信号、判断和资产影响",
            "",
            table(
                ["类型", "原始 ID", "名称或摘要", "状态", "证据等级"],
                reasoning_instance_rows,
            ),
            "",
            "## 6. 当前研究逻辑如何展开",
            "",
            "本章节只根据原 JSON 中已有关系生成局部子图。若某一环节缺失，报告显示“原本体未提供显式关系”，不补链。",
            *judgment_report_lines,
            "",
            "### 链路覆盖提示",
            "",
            f"- 未连接到判断输出的假设：{list_or_none(reasoning_catalog['coverage']['unlinked_hypotheses'])}。",
            f"- 未连接到判断输出的资产影响：{list_or_none(reasoning_catalog['coverage']['unlinked_asset_impacts'])}。",
            "",
            "## 7. 哪些内容可信，哪些还需验证",
            "",
            "本章节只复述原 JSON 的治理状态，不自行判断可信或不可信。",
            "",
            "### 7.1 状态与证据分布",
            "",
            table(
                ["项目", "报告统计"],
                [
                    ["对象记录状态", distribution_text(object_status_counts)],
                    ["关系记录状态", distribution_text(relation_status_counts)],
                    ["对象证据等级", distribution_text(object_evidence_counts)],
                    ["关系证据等级", distribution_text(relation_evidence_counts)],
                    [
                        "来源材料可靠性",
                        distribution_text(
                            governance_summary["source_documents"]["by_reliability"]
                        ),
                    ],
                    [
                        "证据主张等级",
                        distribution_text(
                            governance_summary["evidence_claims"]["by_evidence_level"]
                        ),
                    ],
                ],
            ),
            "",
            "### 7.2 摘要数组与权威对象图一致性",
            "",
            table(
                ["摘要数组", "对象类型", "objects数", "摘要数", "结果", "摘要缺失ID", "摘要额外ID"],
                consistency_rows,
            ),
            "",
            "### 7.3 缺失证据",
            "",
            table_or_none(["缺口", "重要性", "建议材料"], missing_rows),
            "",
            "### 7.4 人工审核项",
            "",
            table_or_none(["项目", "原因", "建议角色"], review_rows),
            "",
            "### 7.5 未解析关系",
            "",
            table_or_none(
                ["关系 ID", "关系类型", "源对象", "目标对象", "状态", "证据等级"],
                unresolved_relation_rows,
            ),
            "",
            "## 8. 研究员阅读提示",
            "",
            "- 原本体中所有对象的 `recordStatus` 均为 `candidate`，因此正文将其解释为候选记录，不写成已确认知识。",
            f"- 原本体中有 {len(unbound_observations)} 个观测对象没有绑定状态变量：{list_or_none(unbound_observations)}。",
            f"- 原本体中有 {len(inconsistent_summaries)} 个摘要数组与权威对象图不一致，推理时应以 `objects + relations` 为准。",
            f"- 缺失证据项数量：{len(ontology.get('missing_evidence', []))}；人工审核项数量：{len(ontology.get('human_review_required', []))}。",
            "- 报告中的传导图是阅读投影；若要执行机器推理，应回到原始关系 ID 或本目录中的机器可读 JSON。",
            "- 本报告不输出投资建议、目标价、收益率预测或仓位建议。",
            "",
            "## 9. 技术追溯附录",
            "",
            "### 9.1 文件与 schema 来源",
            "",
            table(
                ["项目", "路径"],
                [
                    ["原始 JSON", str(args.input_json.resolve())],
                    ["对象 schema", str((args.core_schema_dir / "objects.yaml").resolve())],
                    ["关系 schema", str((args.core_schema_dir / "relations.yaml").resolve())],
                    ["动作 schema", str((args.core_schema_dir / "actions.yaml").resolve())],
                    ["权威对象图", "optimized_ontology.objects"],
                    ["权威关系图", "optimized_ontology.relations"],
                ],
            ),
            "",
            "### 9.2 机器可读伴随文件",
            "",
            table(
                ["文件", "用途"],
                [
                    ["manifest.json", "解析清单、规模统计和权威规则"],
                    ["axiom_catalog.json", "类型能力层机器目录"],
                    ["industry_template_catalog.json", "状态变量和传导模板机器目录"],
                    ["instance_catalog.json", "全部对象实例目录"],
                    ["reasoning_views.json", "判断中心推理链视图"],
                    ["governance_summary.json", "证据、治理和一致性摘要"],
                ],
            ),
            "",
            details_block(
                "查看全部对象 ID 索引",
                table(
                    ["对象 ID", "类型", "名称或摘要", "状态", "证据等级", "治理层"],
                    object_index_rows,
                ),
            ),
            "",
            details_block(
                "查看全部关系 ID 索引",
                table(
                    ["关系 ID", "关系类型", "源对象", "目标对象", "状态", "证据等级"],
                    relation_index_rows,
                ),
            ),
            "",
            details_block(
                "查看来源材料索引",
                table(
                    ["来源 ID", "标题", "发布方", "发布时间", "可靠性", "采纳状态"],
                    source_document_rows,
                ),
            ),
            "",
            details_block(
                "查看证据主张索引",
                table(
                    ["证据 ID", "摘要", "陈述类型", "证据等级", "本体映射"],
                    evidence_claim_rows,
                ),
            ),
        ]
    )
    write_text(output_dir / "ontology_reading_report.md", "\n".join(report_lines))
    write_text(output_dir / "docs" / "ontology_guide.md", "\n".join(report_lines))

    print(f"Generated parsed ontology views in {output_dir}")


if __name__ == "__main__":
    main()
