#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
from typing import Any, Dict, Optional


def build_qa(example: Dict[str, Any], line_idx: int) -> Optional[Dict[str, str]]:
    raw_id = example.get("id")
    dialogue = example.get("dialogue")
    summary = example.get("summary")

    if not isinstance(summary, str):
        return None

    # dialogue 可能是 str 或 list（这里也做兼容）
    if isinstance(dialogue, str):
        dialogue_text = dialogue
    elif isinstance(dialogue, list):
        dialogue_text = "\n".join(str(x) for x in dialogue)
    else:
        return None

    qid = str(raw_id) if raw_id is not None else str(line_idx)

    question = (
        "Summarize the following dialogue concisely while preserving key facts and decisions.\n\n"
        f"Dialogue:\n{dialogue_text}"
    )

    return {"id": qid, "question": question, "answer": summary}


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
    parser = argparse.ArgumentParser(description="Convert dialogue-summary JSONL into {id, question, answer} JSONL.")
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    args = parser.parse_args()
    convert_jsonl(args.input, args.output)


if __name__ == "__main__":
    main()
