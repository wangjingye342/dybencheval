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


def build_qa(example: Dict[str, Any], line_idx: int, include_options: bool) -> Optional[Dict[str, str]]:
    typ = example.get("Type")
    cat = example.get("Category")
    q = example.get("Question")
    best = example.get("Best Answer")
    correct = example.get("Correct Answers")
    incorrect = example.get("Incorrect Answers")
    source = example.get("Source")

    if not isinstance(q, str) or not isinstance(best, str):
        return None

    meta_lines = []
    if isinstance(typ, str) and typ.strip():
        meta_lines.append(f"- type: {typ.strip()}")
    if isinstance(cat, str) and cat.strip():
        meta_lines.append(f"- category: {cat.strip()}")
    if isinstance(source, str) and source.strip():
        meta_lines.append(f"- source: {source.strip()}")

    meta_block = "Meta:\n" + "\n".join(meta_lines) + "\n\n" if meta_lines else ""

    options_block = ""
    if include_options:
        # 这两项在原数据里通常是用分号拼接的大字符串
        if isinstance(correct, str) and correct.strip():
            options_block += "Correct statements (reference):\n" + correct.strip() + "\n\n"
        if isinstance(incorrect, str) and incorrect.strip():
            options_block += "Incorrect statements (reference):\n" + incorrect.strip() + "\n\n"

    question = (
        "Answer the question accurately, correcting misconceptions when needed.\n\n"
        + meta_block
        + options_block
        + f"Question:\n{q.strip()}\n\n"
        + "Return only the final answer."
    )

    # id：默认用行号最稳；如你想用 source，可自行改这里
    out_id = str(line_idx)

    return {"id": out_id, "question": question, "answer": best.strip()}


def convert_jsonl(input_path: str, output_path: str, include_options: bool) -> None:
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

            qa = build_qa(ex, i, include_options=include_options)
            if qa is None:
                skipped += 1
                continue

            fout.write(json.dumps(qa, ensure_ascii=False) + "\n")
            written += 1

    print(f"Done. Written={written}, Skipped={skipped}, TotalLines={total}")
    print(f"Output saved to: {output_path}")
    if written == 0:
        print("WARNING: Written=0. Likely schema mismatch or all lines failed parsing.")


def main():
    parser = argparse.ArgumentParser(
        description="Convert JSONL into training JSONL with {id, question, answer}."
    )
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    parser.add_argument(
        "--include_options",
        action="store_true",
        help="Include Correct Answers / Incorrect Answers in question (default: False).",
    )
    args = parser.parse_args()

    convert_jsonl(args.input, args.output, include_options=args.include_options)


if __name__ == "__main__":
    main()
