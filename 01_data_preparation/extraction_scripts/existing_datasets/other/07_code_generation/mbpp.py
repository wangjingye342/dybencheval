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


def build_qa(example: Dict[str, Any], line_idx: int, include_tests: bool = True) -> Optional[Dict[str, str]]:
    task_id = example.get("task_id")
    prompt = example.get("prompt")
    code = example.get("code")
    test_imports = example.get("test_imports")
    test_list = example.get("test_list")
    source_file = example.get("source_file")

    if not isinstance(prompt, str) or not isinstance(code, str):
        return None

    out_id = str(task_id) if task_id is not None else str(line_idx)

    meta_lines: List[str] = []
    if isinstance(source_file, str) and source_file.strip():
        meta_lines.append(f"- source_file: {source_file.strip()}")

    meta_block = ("Meta:\n" + "\n".join(meta_lines) + "\n\n") if meta_lines else ""

    tests_block = ""
    if include_tests:
        # imports
        if isinstance(test_imports, list) and test_imports:
            imports_text = "\n".join(_as_str(x) for x in test_imports)
            tests_block += "Test imports:\n" + imports_text + "\n\n"

        # asserts
        if isinstance(test_list, list) and test_list:
            # 避免太长：一般不会特别长，这里完整保留；你若想截断可改
            asserts_text = "\n".join(_as_str(x) for x in test_list)
            tests_block += "Unit tests:\n" + asserts_text + "\n\n"

    question = (
        "Write Python code that satisfies the following requirement.\n\n"
        + meta_block
        + "Problem:\n"
        + prompt.strip()
        + ("\n\n" + tests_block.strip() if tests_block.strip() else "")
        + "\n\nReturn only the code."
    )

    answer = code.strip()

    return {"id": out_id, "question": question, "answer": answer}


def convert_jsonl(input_path: str, output_path: str, include_tests: bool = True) -> None:
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

            qa = build_qa(ex, i, include_tests=include_tests)
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
        description="Convert code-generation JSONL into training JSONL with {id, question, answer}."
    )
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    parser.add_argument(
        "--no_tests",
        action="store_true",
        help="Do NOT include test_imports/test_list in question (default: include).",
    )
    args = parser.parse_args()

    convert_jsonl(args.input, args.output, include_tests=(not args.no_tests))


if __name__ == "__main__":
    main()
