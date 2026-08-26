#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
from typing import Any, Dict, Optional, Tuple, List


LABEL_SET = {"positive", "negative", "neutral"}


def _as_str(x: Any) -> str:
    if isinstance(x, str):
        return x
    return json.dumps(x, ensure_ascii=False)


def _find_label_and_text(example: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    """
    适配你这个文件的“异常表头”结构：
      {
        "neutral": "positive",
        "<very long header sentence>": "<text sentence>"
      }

    返回 (label, text)
    """
    if not isinstance(example, dict) or len(example) < 2:
        return None

    label: Optional[str] = None
    text_parts: List[str] = []

    # 1) 先找 label：优先找 value 属于 positive/negative/neutral 的字段
    for k, v in example.items():
        if isinstance(v, str):
            vv = v.strip().lower()
            if vv in LABEL_SET:
                label = vv
                continue

    # 2) 找 text：把“非 label 字段”的字符串 value 当作文本
    #    （你这个数据里通常就 1 个）
    for k, v in example.items():
        if isinstance(v, str):
            vv = v.strip()
            if vv and vv.lower() not in LABEL_SET:
                text_parts.append(vv)

    if label is None or not text_parts:
        return None

    text = "\n".join(text_parts).strip()
    return label, text


def build_qa(example: Dict[str, Any], line_idx: int) -> Optional[Dict[str, str]]:
    res = _find_label_and_text(example)
    if res is None:
        return None
    label, text = res

    question = (
        "Classify the sentiment of the following text as one of: positive, negative, neutral.\n\n"
        f"Text:\n{text}\n\n"
        "Return only one label: positive / negative / neutral."
    )

    return {"id": str(line_idx), "question": question, "answer": label}


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
        print("WARNING: Written=0. Likely schema mismatch or label/text parsing failed.")


def main():
    parser = argparse.ArgumentParser(
        description="Convert JSONL into training JSONL with {id, question, answer}."
    )
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    args = parser.parse_args()

    convert_jsonl(args.input, args.output)


if __name__ == "__main__":
    main()
