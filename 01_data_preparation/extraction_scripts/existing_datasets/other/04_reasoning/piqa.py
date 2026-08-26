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


def _collect_solutions(example: Dict[str, Any]) -> List[Tuple[int, str]]:
    """
    收集 sol1/sol2/...，按数字排序返回 [(n, text), ...]
    """
    sols: List[Tuple[int, str]] = []
    for k, v in example.items():
        m = re.fullmatch(r"sol(\d+)", str(k))
        if not m:
            continue
        idx = int(m.group(1))
        if isinstance(v, str) and v.strip():
            sols.append((idx, v.strip()))
        elif v is not None:
            s = _as_str(v).strip()
            if s:
                sols.append((idx, s))
    sols.sort(key=lambda x: x[0])
    return sols


def convert_one(example: Dict[str, Any], line_idx: int, mode: str) -> Optional[List[Dict[str, str]]]:
    goal = example.get("goal")
    if not isinstance(goal, str) or not goal.strip():
        return None

    sols = _collect_solutions(example)
    if not sols:
        return None

    raw_id = example.get("id")
    base_id = str(raw_id) if raw_id is not None else str(line_idx)

    question = (
        "Please provide a helpful solution to achieve the goal.\n\n"
        f"Goal:\n{goal.strip()}"
    )

    if mode == "concat":
        answer = "\n".join([f"- {s}" for _, s in sols]).strip()
        return [{"id": base_id, "question": question, "answer": answer}]

    # mode == "split"
    out: List[Dict[str, str]] = []
    for j, (sol_idx, sol_text) in enumerate(sols):
        out.append(
            {
                "id": f"{base_id}_sol{sol_idx}",
                "question": question,
                "answer": sol_text,
            }
        )
    return out


def convert_jsonl(input_path: str, output_path: str, mode: str) -> None:
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

            qas = convert_one(ex, i, mode=mode)
            if not qas:
                skipped += 1
                continue

            for qa in qas:
                fout.write(json.dumps(qa, ensure_ascii=False) + "\n")
                written += 1

    print(f"Done. Written={written}, Skipped={skipped}, TotalLines={total}")
    print(f"Output saved to: {output_path}")
    if written == 0:
        print("WARNING: Written=0. Likely schema mismatch or JSON parsing issues.")


def main():
    parser = argparse.ArgumentParser(
        description="Convert goal/sol* JSONL into training JSONL with {id, question, answer}."
    )
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    parser.add_argument(
        "--mode",
        choices=["split", "concat"],
        default="split",
        help="split: one sample per sol*. concat: merge all sol* into one answer.",
    )
    args = parser.parse_args()

    convert_jsonl(args.input, args.output, mode=args.mode)


if __name__ == "__main__":
    main()
