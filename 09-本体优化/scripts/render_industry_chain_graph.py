#!/usr/bin/env python3
"""Render a static industry-chain SVG from an ontology JSON file."""

from __future__ import annotations

import argparse
import html
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SEGMENT_ORDER = [
    "SEG-20260601-001",
    "SEG-20260601-002",
    "SEG-20260601-003",
    "SEG-20260601-004",
    "SEG-20260601-005",
    "SEG-20260601-601",
    "SEG-20260601-602",
    "SEG-20260601-603",
    "SEG-20260601-604",
    "SEG-20260601-605",
    "SEG-20260601-606",
    "SEG-20260601-607",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", type=Path)
    parser.add_argument("--output-svg", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser.parse_args()


def load_ontology(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        source = json.load(handle)
    if "optimized_ontology" in source:
        return source["optimized_ontology"]
    if "ontology_bundle" in source:
        bundle = source["ontology_bundle"]
        objects_module = bundle.get("objects", {})
        relations_module = bundle.get("relations", {})
        objects: list[dict[str, Any]] = []
        relations: list[dict[str, Any]] = []
        if isinstance(objects_module, list):
            objects = [item for item in objects_module if isinstance(item, dict)]
        elif isinstance(objects_module, dict):
            for item in objects_module.values():
                if isinstance(item, list):
                    objects.extend(entry for entry in item if isinstance(entry, dict))
        if isinstance(relations_module, list):
            relations = [item for item in relations_module if isinstance(item, dict)]
        elif isinstance(relations_module, dict):
            for item in relations_module.values():
                if isinstance(item, list):
                    relations.extend(entry for entry in item if isinstance(entry, dict))
        return {"objects": objects, "relations": relations}
    raise KeyError("input JSON must contain optimized_ontology or ontology_bundle")


def label(obj: dict[str, Any] | None, fallback: str = "") -> str:
    if not obj:
        return fallback
    fields = obj.get("fields", {})
    for key in ("name", "title", "templateName", "description"):
        if fields.get(key):
            return str(fields[key])
    return str(obj.get("id", fallback))


def wrap_text(text: str, max_chars: int = 18, max_lines: int = 3) -> list[str]:
    text = " ".join(str(text).split())
    if not text:
        return []
    lines: list[str] = []
    current = ""
    for token in text.replace("/", "/ ").replace("，", "， ").split():
        candidate = token if not current else current + " " + token
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = token
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if len(lines[-1]) > max_chars - 1:
            lines[-1] = lines[-1][: max_chars - 1]
        lines[-1] += "…"
    return lines


def shorten(text: str, limit: int = 20) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def xml(text: Any) -> str:
    return html.escape(str(text), quote=True)


def count_by_segment(
    relations: list[dict[str, Any]],
    relation_type: str,
) -> dict[str, list[str]]:
    by_segment: dict[str, list[str]] = defaultdict(list)
    for relation in relations:
        if relation.get("type") == relation_type:
            by_segment[relation.get("targetId", "")].append(relation.get("sourceId", ""))
    return by_segment


def relation_property(relation: dict[str, Any], key: str, fallback: str = "") -> str:
    value = relation.get("properties", {}).get(key, fallback)
    return str(value) if value is not None else fallback


def render_svg(ontology: dict[str, Any], input_path: Path) -> str:
    objects = ontology.get("objects", [])
    relations = ontology.get("relations", [])
    objects_by_id = {obj["id"]: obj for obj in objects}

    industry = next((obj for obj in objects if obj.get("type") == "Industry"), None)
    segments = [obj for obj in objects if obj.get("type") == "Segment"]
    segment_by_id = {obj["id"]: obj for obj in segments}
    ordered_segments = [
        segment_by_id[segment_id]
        for segment_id in SEGMENT_ORDER
        if segment_id in segment_by_id
    ]
    ordered_segments.extend(
        obj for obj in segments if obj["id"] not in {item["id"] for item in ordered_segments}
    )

    companies_by_segment = count_by_segment(relations, "companyParticipatesInSegment")
    products_by_segment = count_by_segment(relations, "productBelongsToSegment")
    materials_by_segment = count_by_segment(relations, "materialUsedInSegment")

    company_assets: dict[str, list[str]] = defaultdict(list)
    for relation in relations:
        if relation.get("type") == "companyLinkedToAsset":
            company_assets[relation.get("sourceId", "")].append(relation.get("targetId", ""))
    assets_by_segment: dict[str, list[str]] = defaultdict(list)
    for segment_id, company_ids in companies_by_segment.items():
        seen: set[str] = set()
        for company_id in company_ids:
            for asset_id in company_assets.get(company_id, []):
                if asset_id not in seen:
                    assets_by_segment[segment_id].append(asset_id)
                    seen.add(asset_id)

    metadata = ontology.get("ontology_metadata", {})
    industry_context = ontology.get("industry_context", {})
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")

    def object_ref(obj: dict[str, Any] | None) -> str:
        if not obj:
            return "原本体未提供"
        return f"{obj.get('id', '')} {shorten(label(obj), 18)}"

    width = 1800
    header_h = 190
    card_w = 520
    card_h = 310
    gap_x = 34
    gap_y = 34
    left = 56
    top = header_h + 64
    cols = 3
    rows = (len(ordered_segments) + cols - 1) // cols
    height = top + rows * card_h + (rows - 1) * gap_y + 112
    segment_positions: dict[str, tuple[int, int]] = {}
    for index, segment in enumerate(ordered_segments):
        col = index % cols
        row = index // cols
        segment_positions[segment["id"]] = (
            left + col * (card_w + gap_x),
            top + row * (card_h + gap_y),
        )
    segment_connect_relations = [
        relation
        for relation in relations
        if relation.get("type") == "segmentConnectsToSegment"
        and relation.get("sourceId") in segment_positions
        and relation.get("targetId") in segment_positions
    ]

    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        "<style><![CDATA[",
        "text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',Arial,sans-serif;fill:#17202a}",
        ".title{font-size:34px;font-weight:760}",
        ".subtitle{font-size:16px;fill:#526070}",
        ".small{font-size:13px;fill:#667586}",
        ".tag{font-size:12px;fill:#334155;font-weight:650}",
        ".cardTitle{font-size:19px;font-weight:740}",
        ".cardId{font-size:12px;fill:#64748b;font-weight:650}",
        ".section{font-size:13px;font-weight:760;fill:#334155}",
        ".item{font-size:12px;fill:#17202a}",
        ".muted{font-size:12px;fill:#8a96a5}",
        ".line{stroke:#cbd5e1;stroke-width:1.4;fill:none}",
        ".edge{stroke:#475569;stroke-width:2;fill:none;marker-end:url(#arrowhead)}",
        ".edgeLabel{font-size:12px;fill:#334155;font-weight:700}",
        ".dash{stroke:#94a3b8;stroke-width:1.2;stroke-dasharray:5 5;fill:none}",
        "]]></style>",
        '<marker id="arrowhead" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">',
        '<path d="M0,0 L0,6 L9,3 z" fill="#475569"/>',
        "</marker>",
        "</defs>",
        f'<rect x="0" y="0" width="{width}" height="100%" fill="#f7f9fb"/>',
        f'<rect x="32" y="28" width="{width - 64}" height="126" rx="12" fill="#ffffff" stroke="#d7dee8"/>',
        f'<text x="56" y="72" class="title">{xml(label(industry, "半导体产业"))} v{xml(metadata.get("ontology_version", ""))} 产业链图谱</text>',
        f'<text x="56" y="105" class="subtitle">静态阅读投影：只使用 v4 原始 objects / relations；不补充外部产业链知识。源文件：{xml(input_path.name)}</text>',
        f'<text x="56" y="132" class="small">研究问题：{xml(industry_context.get("research_question", ""))}</text>',
        f'<text x="{width - 360}" y="72" class="small">生成时间：{xml(generated_at)}</text>',
        '<g transform="translate(56 168)">',
        '<rect x="0" y="0" width="282" height="38" rx="8" fill="#e8f2ff" stroke="#9cc6f2"/>',
        f'<text x="14" y="25" class="tag">Industry：{xml(object_ref(industry))}</text>',
        '<rect x="318" y="0" width="282" height="38" rx="8" fill="#fff7ed" stroke="#fdba74"/>',
        f'<text x="332" y="25" class="tag">环节箭头：segmentConnectsToSegment {len(segment_connect_relations)}</text>',
        '<rect x="636" y="0" width="338" height="38" rx="8" fill="#f0fdf4" stroke="#86efac"/>',
        '<text x="650" y="25" class="tag">资产：公司→资产二跳阅读投影</text>',
        '<rect x="1010" y="0" width="398" height="38" rx="8" fill="#f8fafc" stroke="#cbd5e1"/>',
        '<text x="1024" y="25" class="tag">空项显示“原本体未提供显式连接”</text>',
        "</g>",
    ]

    industry_x = width / 2
    industry_y = header_h + 8
    parts.append(
        f'<circle cx="{industry_x:.0f}" cy="{industry_y:.0f}" r="8" fill="#2563eb"/>'
    )

    def edge_points(source_id: str, target_id: str) -> tuple[float, float, float, float]:
        sx, sy = segment_positions[source_id]
        tx, ty = segment_positions[target_id]
        scx = sx + card_w / 2
        scy = sy + card_h / 2
        tcx = tx + card_w / 2
        tcy = ty + card_h / 2
        dx = tcx - scx
        dy = tcy - scy
        if abs(dx) >= abs(dy):
            start_x = sx + card_w if dx >= 0 else sx
            start_y = scy
            end_x = tx if dx >= 0 else tx + card_w
            end_y = tcy
        else:
            start_x = scx
            start_y = sy + card_h if dy >= 0 else sy
            end_x = tcx
            end_y = ty if dy >= 0 else ty + card_h
        return start_x, start_y, end_x, end_y

    def add_text_lines(x: int, y: int, lines: list[str], klass: str, line_h: int) -> int:
        for line in lines:
            parts.append(f'<text x="{x}" y="{y}" class="{klass}">{xml(line)}</text>')
            y += line_h
        return y

    palette = [
        ("#eef6ff", "#93c5fd"),
        ("#f8fafc", "#cbd5e1"),
        ("#f0fdf4", "#86efac"),
        ("#fff7ed", "#fdba74"),
        ("#fef2f2", "#fca5a5"),
        ("#f5f3ff", "#c4b5fd"),
    ]

    for segment in ordered_segments:
        x, y = segment_positions[segment["id"]]
        center_x = x + card_w / 2
        parts.append(
            f'<path d="M {industry_x:.0f} {industry_y + 10:.0f} C {industry_x:.0f} {industry_y + 44:.0f}, {center_x:.0f} {y - 34:.0f}, {center_x:.0f} {y:.0f}" class="line"/>'
        )

    for relation in segment_connect_relations:
        source_id = relation["sourceId"]
        target_id = relation["targetId"]
        start_x, start_y, end_x, end_y = edge_points(source_id, target_id)
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        label_text = relation_property(relation, "chainRelationType", relation.get("id", ""))
        parts.append(
            f'<path d="M {start_x:.0f} {start_y:.0f} C {mid_x:.0f} {start_y:.0f}, {mid_x:.0f} {end_y:.0f}, {end_x:.0f} {end_y:.0f}" class="edge"/>'
        )
        parts.append(
            f'<text x="{mid_x + 8:.0f}" y="{mid_y - 8:.0f}" class="edgeLabel">{xml(shorten(label_text, 18))}</text>'
        )

    for index, segment in enumerate(ordered_segments):
        x, y = segment_positions[segment["id"]]
        fill, stroke = palette[index % len(palette)]
        parts.append(
            f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>'
        )
        parts.append(
            f'<text x="{x + 18}" y="{y + 29}" class="cardTitle">{xml(shorten(label(segment), 28))}</text>'
        )
        parts.append(
            f'<text x="{x + 18}" y="{y + 50}" class="cardId">{xml(segment["id"])} · segmentBelongsToIndustry</text>'
        )

        y_cursor = y + 80
        sections = [
            ("公司", companies_by_segment.get(segment["id"], []), "#0f766e"),
            ("产品", products_by_segment.get(segment["id"], []), "#6d28d9"),
            ("材料", materials_by_segment.get(segment["id"], []), "#b45309"),
            ("资产(经公司二跳)", assets_by_segment.get(segment["id"], []), "#475569"),
        ]
        for section_title, ids, color in sections:
            parts.append(
                f'<text x="{x + 18}" y="{y_cursor}" class="section" fill="{color}">{xml(section_title)} · {len(ids)}</text>'
            )
            y_cursor += 18
            if ids:
                names = [label(objects_by_id.get(item_id), item_id) for item_id in ids]
                line = "、".join(shorten(name, 16) for name in names)
                text_lines = wrap_text(line, max_chars=52, max_lines=2)
                y_cursor = add_text_lines(x + 18, y_cursor, text_lines, "item", 16)
            else:
                parts.append(
                    f'<text x="{x + 18}" y="{y_cursor}" class="muted">原本体未提供显式连接</text>'
                )
                y_cursor += 16
            y_cursor += 10

    note_y = height - 62
    parts.extend(
        [
            f'<text x="56" y="{note_y}" class="small">追溯说明：Segment 卡片来自 `Segment` 对象；公司/产品/材料分别来自 `companyParticipatesInSegment`、`productBelongsToSegment`、`materialUsedInSegment`；资产为 `companyParticipatesInSegment + companyLinkedToAsset` 二跳阅读投影。</text>',
            f'<text x="56" y="{note_y + 24}" class="small">环节箭头只来自 `segmentConnectsToSegment`；若原本体没有该关系，本图不会用常识或 positionInChain 补链。该图不代表行业完整图谱。</text>',
            "</svg>",
        ]
    )
    return "\n".join(parts)


def render_md(ontology: dict[str, Any], input_path: Path, output_svg: Path) -> str:
    objects = ontology.get("objects", [])
    relations = ontology.get("relations", [])
    objects_by_id = {obj["id"]: obj for obj in objects}

    companies_by_segment = count_by_segment(relations, "companyParticipatesInSegment")
    products_by_segment = count_by_segment(relations, "productBelongsToSegment")
    materials_by_segment = count_by_segment(relations, "materialUsedInSegment")
    segment_edges = [
        relation
        for relation in relations
        if relation.get("type") == "segmentConnectsToSegment"
        and relation.get("sourceId") in objects_by_id
        and relation.get("targetId") in objects_by_id
    ]

    rows = []
    for segment in [obj for obj in objects if obj.get("type") == "Segment"]:
        segment_id = segment["id"]
        rows.append(
            [
                segment_id,
                label(segment),
                "、".join(label(objects_by_id.get(item), item) for item in companies_by_segment.get(segment_id, []))
                or "原本体未提供",
                "、".join(label(objects_by_id.get(item), item) for item in products_by_segment.get(segment_id, []))
                or "原本体未提供",
                "、".join(label(objects_by_id.get(item), item) for item in materials_by_segment.get(segment_id, []))
                or "原本体未提供",
            ]
        )

    def md_cell(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    table_lines = [
        "| Segment ID | 环节名称 | 公司 | 产品 | 材料 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        table_lines.append("| " + " | ".join(md_cell(cell) for cell in row) + " |")

    edge_lines = [
        "| 关系 ID | 源环节 | 关系语义 | 目标环节 |",
        "| --- | --- | --- | --- |",
    ]
    if segment_edges:
        for relation in segment_edges:
            edge_lines.append(
                "| "
                + " | ".join(
                    md_cell(cell)
                    for cell in [
                        relation.get("id", ""),
                        label(objects_by_id.get(relation.get("sourceId", "")), relation.get("sourceId", "")),
                        relation_property(relation, "chainRelationType", "未提供"),
                        label(objects_by_id.get(relation.get("targetId", "")), relation.get("targetId", "")),
                    ]
                )
                + " |"
            )
    else:
        edge_lines.append("| 原本体未提供 | 原本体未提供 | 原本体未提供显式环节连接 | 原本体未提供 |")

    return "\n".join(
        [
            "# v4 产业链图谱追溯说明",
            "",
            f"- 原始文件：`{input_path}`",
            f"- 静态图谱：`{output_svg.name}`",
            "- 权威数据：`optimized_ontology.objects` 与 `optimized_ontology.relations`",
            "- 一跳关系：`segmentBelongsToIndustry`、`companyParticipatesInSegment`、`productBelongsToSegment`、`materialUsedInSegment`、`segmentConnectsToSegment`",
            "- 资产为二跳阅读投影：`companyParticipatesInSegment + companyLinkedToAsset`",
            "- 图谱不补充原 JSON 中不存在的产业链环节、公司、产品、材料或关系；没有 `segmentConnectsToSegment` 时不生成环节箭头。",
            "",
            "## 显式环节连接",
            "",
            *edge_lines,
            "",
            "## 环节关系明细",
            "",
            *table_lines,
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    ontology = load_ontology(args.input_json)
    args.output_svg.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_svg.write_text(render_svg(ontology, args.input_json), encoding="utf-8")
    args.output_md.write_text(
        render_md(ontology, args.input_json, args.output_svg), encoding="utf-8"
    )
    print(f"Generated {args.output_svg}")
    print(f"Generated {args.output_md}")


if __name__ == "__main__":
    main()
