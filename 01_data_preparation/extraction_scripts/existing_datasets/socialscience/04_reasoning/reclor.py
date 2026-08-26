#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
from typing import Any, Dict, List, Optional


def _as_str(x: Any) -> str:
    if isinstance(x, str):
        return x
    return json.dumps(x, ensure_ascii=False)


def _normalize_label(label: Any, n: int) -> Optional[int]:
    """
    兼容 label：
    - 0-based: 0..n-1
    - 1-based: 1..n  -> 转成 0..n-1
    """
    if isinstance(label, bool):
        return None

    if isinstance(label, int):
        v = label
    elif isinstance(label, str) and label.strip().isdigit():
        v = int(label.strip())
    else:
        return None

    if 0 <= v < n:
        return v
    if 1 <= v <= n:
        return v - 1
    return None


def build_qa(example: Dict[str, Any], line_idx: int) -> Optional[Dict[str, str]]:
    context = example.get("context")
    q = example.get("question")
    answers = example.get("answers")
    label = example.get("label")

    if not isinstance(context, str) or not isinstance(q, str) or not isinstance(answers, list) or not answers:
        return None

    # 选项转字符串
    opts: List[str] = []
    for a in answers:
        s = _as_str(a).strip()
        opts.append(s)

    idx = _normalize_label(label, len(opts))
    if idx is None:
        return None

    # question 模板
    option_lines = [f"{i}. {opt}" for i, opt in enumerate(opts)]
    question = (
        "Answer the question based on the context. Choose the best option.\n\n"
        f"Context:\n{context.strip()}\n\n"
        f"Question:\n{q.strip()}\n\n"
        "Options:\n" + "\n".join(option_lines) + "\n\n"
        "Return only the final answer."
    )

    answer = opts[idx]

    # id：优先 id_string，其次 id，最后行号
    raw_id = example.get("id_string")
    if raw_id is None:
        raw_id = example.get("id")
    out_id = str(raw_id) if raw_id is not None else str(line_idx)

    return {"id": out_id, "question": question, "answer": answer}


def convert_jsonl(input_path: str, output_path: str) -> None:
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

            qa = build_qa(ex, i)
            if qa is None:
                skipped += 1
                continue

            fout.write(json.dumps(qa, ensure_ascii=False) + "\n")
            written += 1

    print(f"Done. Written={written}, Skipped={skipped}, TotalLines={total}")
    print(f"Output saved to: {output_path}")
    if written == 0:
        print("WARNING: Written=0. Likely schema mismatch or label/options parsing failed.")


def main():
    parser = argparse.ArgumentParser(
        description="Convert JSONL dataset into training JSONL with {id, question, answer}."
    )
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    args = parser.parse_args()

    convert_jsonl(args.input, args.output)


if __name__ == "__main__":
    main()
