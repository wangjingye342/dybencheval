#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple


def _as_str(x: Any) -> str:
    if isinstance(x, str):
        return x
    return json.dumps(x, ensure_ascii=False)


def _collect_answer_options(example: Dict[str, Any]) -> List[Tuple[int, str]]:
    """
    收集 answer0/answer1/...，按数字排序，返回 [(idx, text), ...]
    """
    opts: List[Tuple[int, str]] = []
    for k, v in example.items():
        m = re.fullmatch(r"answer(\d+)", str(k))
        if not m:
            continue
        idx = int(m.group(1))
        opts.append((idx, _as_str(v)))
    opts.sort(key=lambda x: x[0])
    return opts


def _normalize_label(label: Any, n_opts: int) -> Optional[int]:
    """
    label 兼容：
    - 0-based: 0..n-1
    - 1-based: 1..n   -> 转成 0..n-1
    """
    if isinstance(label, bool):
        return None
    if isinstance(label, str):
        label = label.strip()
        if not label.isdigit():
            return None
        label_int = int(label)
    elif isinstance(label, int):
        label_int = label
    else:
        return None

    if 0 <= label_int < n_opts:
        return label_int
    if 1 <= label_int <= n_opts:
        return label_int - 1
    return None


def build_qa(example: Dict[str, Any], line_idx: int) -> Optional[Dict[str, str]]:
    ctx = example.get("context")
    q = example.get("question")
    label = example.get("label")

    if not isinstance(ctx, str) or not isinstance(q, str):
        return None

    opts = _collect_answer_options(example)
    if not opts:
        return None

    norm = _normalize_label(label, len(opts))
    if norm is None:
        return None

    # 将选项展示为 0/1/2...（也可以改成 A/B/C）
    option_lines = [f"{i}. {text}" for i, (_, text) in enumerate(opts)]

    question = (
        "Answer the question based on the context. Choose the best option.\n\n"
        f"Context:\n{ctx.strip()}\n\n"
        f"Question:\n{q.strip()}\n\n"
        "Options:\n" + "\n".join(option_lines)
    )

    answer = opts[norm][1].strip()

    raw_id = example.get("id")
    out_id = str(raw_id) if raw_id is not None else str(line_idx)

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
