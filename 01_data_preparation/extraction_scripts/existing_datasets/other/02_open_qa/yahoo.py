#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
from typing import Any, Dict, Optional


def build_qa(example: Dict[str, Any], line_idx: int) -> Optional[Dict[str, str]]:
    q = example.get("question")
    a = example.get("answer")

    if not isinstance(q, str) or not isinstance(a, str):
        return None

    # 原始如果有 id 就用，否则用行号
    raw_id = example.get("id")
    qid = str(raw_id) if raw_id is not None else str(line_idx)

    return {"id": qid, "question": q, "answer": a}


def convert_jsonl(input_path: str, output_path: str) -> None:
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

            qa = build_qa(ex, i)
            if qa is None:
                skipped += 1
                continue

            fout.write(json.dumps(qa, ensure_ascii=False) + "\n")
            written += 1

    print(f"Done. Written: {written}, Skipped: {skipped}")
    print(f"Output saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Convert JSONL QA dataset into {id, question, answer}.")
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    args = parser.parse_args()

    convert_jsonl(args.input, args.output)


if __name__ == "__main__":
    main()
