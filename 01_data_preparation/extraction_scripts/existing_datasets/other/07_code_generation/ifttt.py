#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import ast
import json
import os
from typing import Any, Dict, Optional


def _as_str(x: Any) -> str:
    if isinstance(x, str):
        return x
    return json.dumps(x, ensure_ascii=False)


def _safe_parse_maybe_literal(x: Any) -> Any:
    """
    这个数据集里很多字段是“字符串形式的 list/dict”，例如:
      "['weather', 'if_notifications']"
      "[{'id': '...', 'name': '...'}]"
    这里用 ast.literal_eval 安全解析；解析失败就原样返回。
    """
    if not isinstance(x, str):
        return x
    s = x.strip()
    if not s:
        return x
    if s[0] not in "[{(":
        return x
    try:
        return ast.literal_eval(s)
    except Exception:
        return x


def _format_permissions(perms_raw: Any, max_items: int = 6) -> str:
    perms = _safe_parse_maybe_literal(perms_raw)
    if not isinstance(perms, list):
        return ""

    lines = []
    for p in perms[:max_items]:
        if not isinstance(p, dict):
            continue
        pid = p.get("id")
        pname = p.get("name")
        pdesc = p.get("description")
        # 简洁展示
        parts = []
        if pname:
            parts.append(str(pname))
        if pid:
            parts.append(f"({pid})")
        line = " ".join(parts).strip()
        if isinstance(pdesc, str) and pdesc.strip():
            line = (line + ": " + pdesc.strip()).strip()
        if line:
            lines.append(f"- {line}")

    if not lines:
        return ""
    return "Permissions (subset):\n" + "\n".join(lines) + "\n\n"


def build_qa(example: Dict[str, Any], line_idx: int) -> Optional[Dict[str, str]]:
    # id：优先用 id，其次 friendly_id，其次 Unnamed:0，其次行号
    raw_id = example.get("id")
    if raw_id is None:
        raw_id = example.get("friendly_id")
    if raw_id is None:
        raw_id = example.get("Unnamed: 0")
    out_id = str(raw_id) if raw_id is not None else str(line_idx)

    name = example.get("name")
    description = example.get("description")

    if not isinstance(description, str) and not isinstance(name, str):
        return None

    services = _safe_parse_maybe_literal(example.get("services"))
    service_names = _safe_parse_maybe_literal(example.get("service_names"))
    service_triggers = example.get("service_triggers")
    service_actions = _safe_parse_maybe_literal(example.get("service_actions"))
    triggers_category = example.get("triggers_category")
    actions_category = _safe_parse_maybe_literal(example.get("actions_category"))
    speed = example.get("speed")
    installs_count = example.get("installs_count")
    by_service_owner = example.get("by_service_owner")
    requires_android_app = example.get("requires_android_app")
    requires_ios_app = example.get("requires_ios_app")
    requires_mobile_app = example.get("requires_mobile_app")
    permissions_block = _format_permissions(example.get("permissions"))

    # 组装 question（尽量放“对生成描述有用的信息”）
    lines = []
    if isinstance(service_names, list) and service_names:
        lines.append("Service names: " + ", ".join(_as_str(s) for s in service_names))
    elif isinstance(service_names, str) and service_names.strip():
        lines.append("Service names: " + service_names.strip())

    if isinstance(services, list) and services:
        lines.append("Service slugs: " + ", ".join(_as_str(s) for s in services))

    if isinstance(service_triggers, str) and service_triggers.strip():
        lines.append("Trigger service: " + service_triggers.strip())

    if isinstance(service_actions, list) and service_actions:
        lines.append("Action service(s): " + ", ".join(_as_str(s) for s in service_actions))
    elif isinstance(service_actions, str) and service_actions.strip():
        lines.append("Action service(s): " + service_actions.strip())

    if isinstance(triggers_category, str) and triggers_category.strip():
        lines.append("Trigger category: " + triggers_category.strip())

    if isinstance(actions_category, list) and actions_category:
        lines.append("Action category: " + ", ".join(_as_str(s) for s in actions_category))
    elif isinstance(actions_category, str) and actions_category.strip():
        lines.append("Action category: " + actions_category.strip())

    if isinstance(speed, str) and speed.strip():
        lines.append("Speed: " + speed.strip())

    # 一些布尔/统计信息（可选）
    if by_service_owner is not None:
        lines.append(f"By service owner: {bool(by_service_owner)}")
    if requires_mobile_app is not None:
        lines.append(f"Requires mobile app: {bool(requires_mobile_app)}")
    if requires_android_app is not None:
        lines.append(f"Requires Android app: {bool(requires_android_app)}")
    if requires_ios_app is not None:
        lines.append(f"Requires iOS app: {bool(requires_ios_app)}")
    if installs_count is not None:
        lines.append(f"Installs count: {_as_str(installs_count)}")

    info_block = "\n".join(f"- {x}" for x in lines).strip()

    question = (
        "Generate a concise, user-facing IFTTT applet description based on the structured metadata.\n\n"
        "Metadata:\n"
        + (info_block if info_block else "- (no metadata)\n")
        + "\n\n"
        + permissions_block
        + "Return only the final description."
    )

    answer = description.strip() if isinstance(description, str) and description.strip() else (name.strip() if isinstance(name, str) else "")
    if not answer:
        return None

    return {"id": out_id, "question": question, "answer": answer}


def convert_jsonl(input_path: str, output_path: str) -> None:
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    written, skipped = 0, 0
    with open(input_path, "r", encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout:
        for i, line in enumerate(fin):
            line = line.strip()
            if not line:
                skipped += 1
                continue

            try:
                ex = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue

            if not isinstance(ex, dict):
                skipped += 1
                continue

            qa = build_qa(ex, i)
            if qa is None:
                skipped += 1
                continue

            fout.write(json.dumps(qa, ensure_ascii=False) + "\n")
            written += 1

    print(f"Done. Written={written}, Skipped={skipped}")
    print(f"Output saved to: {output_path}")
    if written == 0:
        print("WARNING: Written=0. Likely schema mismatch or parsing issues.")


def main():
    parser = argparse.ArgumentParser(description="Convert IFTTT-like JSONL into training JSONL with {id, question, answer}.")
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    args = parser.parse_args()

    convert_jsonl(args.input, args.output)


if __name__ == "__main__":
    main()
