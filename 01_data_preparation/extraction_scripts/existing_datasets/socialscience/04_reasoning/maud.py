#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
from typing import Any, Dict, Optional


def _as_str(x: Any) -> str:
    if isinstance(x, str):
        return x
    return json.dumps(x, ensure_ascii=False)


def build_qa(example: Dict[str, Any], line_idx: int, id_mode: str, include_label: bool) -> Optional[Dict[str, str]]:
    # required-ish
    text = example.get("text")
    q = example.get("question")
    ans = example.get("answer")

    if not isinstance(text, str) or not isinstance(q, str) or not isinstance(ans, str):
        return None

    ex_id = example.get("id")
    contract_name = example.get("contract_name")

    # id
    if id_mode == "contract" and contract_name is not None and ex_id is not None:
        out_id = f"{_as_str(contract_name)}:{_as_str(ex_id)}"
    elif ex_id is not None:
        out_id = _as_str(ex_id)
    else:
        out_id = str(line_idx)

    # meta
    data_type = example.get("data_type")
    category = example.get("category")
    text_type = example.get("text_type")
    subq = example.get("subquestion")
    label = example.get("label")

    meta_lines = []
    if contract_name is not None:
        meta_lines.append(f"- contract_name: {_as_str(contract_name)}")
    if data_type is not None:
        meta_lines.append(f"- data_type: {_as_str(data_type)}")
    if category is not None:
        meta_lines.append(f"- category: {_as_str(category)}")
    if text_type is not None:
        meta_lines.append(f"- text_type: {_as_str(text_type)}")
    if isinstance(subq, str) and subq.strip() and subq.strip() != "<NONE>":
        meta_lines.append(f"- subquestion: {subq.strip()}")
    if include_label and label is not None:
        meta_lines.append(f"- label: {_as_str(label)}")

    meta_block = ("Meta:\n" + "\n".join(meta_lines) + "\n\n") if meta_lines else ""

    question = (
        "Answer the question using the given contract excerpt.\n\n"
        + meta_block
        + f"Task:\n{q.strip()}\n\n"
        + "Contract excerpt:\n"
        + text.strip()
        + "\n\nReturn only the final answer."
    )

    return {"id": out_id, "question": question, "answer": ans.strip()}


def convert_jsonl(input_path: str, output_path: str, id_mode: str, include_label: bool) -> None:
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    written, skipped, total = 0, 0, 0
    with open(input_path, "r", encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout:
        for i, line in enumerate(fin):
            total += 1
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

            qa = build_qa(ex, i, id_mode=id_mode, include_label=include_label)
            if qa is None:
                skipped += 1
                continue

            fout.write(json.dumps(qa, ensure_ascii=False) + "\n")
            written += 1

    print(f"Done. Written={written}, Skipped={skipped}, TotalLines={total}")
    print(f"Output saved to: {output_path}")
    if written == 0:
        print("WARNING: Written=0. Likely schema mismatch or JSON parsing issues.")


def main():
    parser = argparse.ArgumentParser(
        description="Convert contract QA JSONL into training JSONL with {id, question, answer}."
    )
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    parser.add_argument(
        "--id_mode",
        choices=["raw", "contract"],
        default="raw",
        help="raw: use example.id; contract: use contract_name:id (helps avoid collisions).",
    )
    parser.add_argument(
        "--include_label",
        action="store_true",
        help="Include 'label' field into question metadata (default: False).",
    )
    args = parser.parse_args()

    convert_jsonl(args.input, args.output, id_mode=args.id_mode, include_label=args.include_label)


if __name__ == "__main__":
    main()
