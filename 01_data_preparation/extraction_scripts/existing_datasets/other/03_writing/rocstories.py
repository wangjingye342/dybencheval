#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
from typing import Any, Dict, Optional


def build_qa(example: Dict[str, Any], line_idx: int) -> Optional[Dict[str, str]]:
    title = example.get("storytitle")
    story = example.get("story")

    if not isinstance(title, str) or not isinstance(story, str):
        return None

    raw_id = example.get("Unnamed: 0")
    if raw_id is None:
        raw_id = example.get("id")
    qid = str(raw_id) if raw_id is not None else str(line_idx)

    question = (
        "Write a coherent short story based on the given title.\n\n"
        f"Title: {title}"
    )

    answer = story.strip()
    return {"id": qid, "question": question, "answer": answer}


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
                # 输入里混入了非 JSON 行时会走到这里
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

            if written % 1000 == 0:
                print(f"[progress] written={written}, skipped={skipped}, total_lines_seen={total}")

    print(f"Done. Written={written}, Skipped={skipped}, TotalLines={total}")
    print(f"Output saved to: {output_path}")

    # 额外：如果没写出任何样本，直接给出强提示
    if written == 0:
        print("WARNING: Written=0. This usually means schema mismatch or all lines failed JSON parsing.")


def main():
    parser = argparse.ArgumentParser(description="Convert ROCStories JSONL into {id, question, answer}.")
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    args = parser.parse_args()

    convert_jsonl(args.input, args.output)


if __name__ == "__main__":
    main()
