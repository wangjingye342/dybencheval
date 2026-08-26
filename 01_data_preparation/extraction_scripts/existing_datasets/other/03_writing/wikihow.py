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


def _parse_metadata(meta: Any) -> Dict[str, Any]:
    """
    METADATA 在这个数据集里通常是一个 JSON 字符串：
      '{"url": "...", "language": "en"}'
    解析失败则返回空 dict。
    """
    if isinstance(meta, dict):
        return meta
    if isinstance(meta, str):
        s = meta.strip()
        if not s:
            return {}
        try:
            obj = json.loads(s)
            return obj if isinstance(obj, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def build_qa(example: Dict[str, Any], line_idx: int) -> Optional[Dict[str, str]]:
    instr = example.get("INSTRUCTION")
    resp = example.get("RESPONSE")
    source = example.get("SOURCE")
    meta = _parse_metadata(example.get("METADATA"))

    if not isinstance(instr, str) or not isinstance(resp, str):
        return None

    url = meta.get("url")
    lang = meta.get("language")

    meta_lines = []
    if isinstance(source, str) and source.strip():
        meta_lines.append(f"- source: {source.strip()}")
    if isinstance(url, str) and url.strip():
        meta_lines.append(f"- url: {url.strip()}")
    if isinstance(lang, str) and lang.strip():
        meta_lines.append(f"- language: {lang.strip()}")

    meta_block = ""
    if meta_lines:
        meta_block = "Meta:\n" + "\n".join(meta_lines) + "\n\n"

    question = (
        "Please follow the instruction and provide a helpful response.\n\n"
        + meta_block
        + f"Instruction:\n{instr.strip()}"
    )

    answer = resp.strip()

    return {"id": str(line_idx), "question": question, "answer": answer}


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
        print("WARNING: Written=0. Check schema mismatch or JSON parsing issues.")


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
