#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert a JSONL dataset into training-friendly JSONL with fields:
  - id
  - question  (contains all useful info for the model)
  - answer    (reference answer)

Usage:
  python convert_dataset.py --input input.jsonl --output output.jsonl

Notes:
- Supports common formats such as:
    {"question": "...", "choices": [...], "answer": 1}
    {"question": "...", "options": [...], "answer": "B"}
    {"context": "...", "question": "...", "answer": "..."}
- Easy to customize input field priorities and option formatting below.
"""

import argparse
import json
import string
from typing import Any, Dict, List, Optional, Tuple, Union


# =========================
# Customization Zone
# =========================

# Candidate fields to be merged into "question" (in this order).
QUESTION_FIELD_PRIORITY = [
    "instruction",
    "system",
    "context",
    "passage",
    "background",
    "prompt",
    "stem",
    "question",
    "query",
]

# Candidate fields that represent options / choices.
OPTION_FIELD_CANDIDATES = [
    "choices",
    "options",
    "candidates",
    "answers",   # sometimes datasets use "answers" as option list
]

# Candidate fields that might already provide an id.
ID_FIELD_CANDIDATES = ["id", "qid", "uuid", "question_id", "item_id"]

# If True, include any other non-empty fields (except answer/options) into question.
INCLUDE_EXTRA_FIELDS = True

# Fields to exclude from being merged (besides detected options & answer field).
EXCLUDE_FIELDS = {"answer", "label", "target", "gold", "output"}


# =========================
# Helper functions
# =========================

def is_nonempty_text(x: Any) -> bool:
    return isinstance(x, str) and x.strip() != ""


def normalize_to_text(x: Any) -> str:
    """Convert common Python types to a compact text representation."""
    if x is None:
        return ""
    if isinstance(x, str):
        return x.strip()
    if isinstance(x, (int, float, bool)):
        return str(x)
    # For lists/dicts, keep JSON compact but readable.
    return json.dumps(x, ensure_ascii=False)


def find_first_present(d: Dict[str, Any], keys: List[str]) -> Optional[str]:
    for k in keys:
        if k in d and d[k] is not None and normalize_to_text(d[k]).strip() != "":
            return k
    return None


def extract_id(rec: Dict[str, Any], fallback_index: int) -> str:
    k = find_first_present(rec, ID_FIELD_CANDIDATES)
    if k is not None:
        return normalize_to_text(rec[k])
    return str(fallback_index)


def extract_options(rec: Dict[str, Any]) -> Tuple[Optional[str], Optional[List[Any]]]:
    """Return (option_field_name, options_list) if found."""
    for k in OPTION_FIELD_CANDIDATES:
        if k in rec and isinstance(rec[k], list) and len(rec[k]) > 0:
            return k, rec[k]
    return None, None


def option_labels(n: int) -> List[str]:
    """Generate labels A, B, C...; if >26, use 1,2,3..."""
    if n <= 26:
        return list(string.ascii_uppercase[:n])
    return [str(i + 1) for i in range(n)]


def format_options(options: List[Any]) -> str:
    labels = option_labels(len(options))
    lines = []
    for lab, opt in zip(labels, options):
        lines.append(f"{lab}. {normalize_to_text(opt)}")
    return "Options:\n" + "\n".join(lines)


def resolve_answer(rec: Dict[str, Any], options: Optional[List[Any]]) -> str:
    """
    Convert various answer formats into a reference answer text.
    Supports:
      - int index (0-based or 1-based)
      - letter like "A"/"B"
      - actual answer string
    """
    # Try common answer keys
    answer_key = find_first_present(rec, ["answer", "label", "target", "gold", "output"])
    if answer_key is None:
        return ""

    ans = rec[answer_key]

    # If options exist, try to map indices/letters to option text
    if options is not None and len(options) > 0:
        # int index
        if isinstance(ans, int):
            # Heuristic: if 0 <= ans < len -> 0-based; if 1 <= ans <= len -> 1-based
            if 0 <= ans < len(options):
                return normalize_to_text(options[ans])
            if 1 <= ans <= len(options):
                return normalize_to_text(options[ans - 1])

        # numeric in string
        if isinstance(ans, str) and ans.strip().isdigit():
            idx = int(ans.strip())
            if 0 <= idx < len(options):
                return normalize_to_text(options[idx])
            if 1 <= idx <= len(options):
                return normalize_to_text(options[idx - 1])

        # letter in string
        if isinstance(ans, str) and ans.strip():
            s = ans.strip().upper()
            labels = option_labels(len(options))
            if s in labels:
                pos = labels.index(s)
                return normalize_to_text(options[pos])

    # fallback: keep answer as text
    return normalize_to_text(ans)


def build_question(rec: Dict[str, Any], option_field: Optional[str], options: Optional[List[Any]]) -> str:
    parts: List[str] = []

    # 1) Merge prioritized fields
    used_keys = set()
    for k in QUESTION_FIELD_PRIORITY:
        if k in rec and rec[k] is not None:
            txt = normalize_to_text(rec[k])
            if txt.strip():
                parts.append(txt)
                used_keys.add(k)

    # 2) Optionally merge extra fields (excluding answer/options/empty)
    if INCLUDE_EXTRA_FIELDS:
        for k, v in rec.items():
            if k in used_keys:
                continue
            if k in EXCLUDE_FIELDS:
                continue
            if option_field is not None and k == option_field:
                continue
            txt = normalize_to_text(v)
            if txt.strip():
                parts.append(f"{k}: {txt}")

    # 3) Append formatted options
    if options is not None:
        parts.append(format_options(options))

    # Clean join
    question = "\n\n".join([p.strip() for p in parts if p.strip()])
    return question.strip()


# =========================
# Main conversion
# =========================

def convert_jsonl(input_path: str, output_path: str) -> None:
    n_in = 0
    n_out = 0

    with open(input_path, "r", encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout:
        for idx, line in enumerate(fin, start=1):
            line = line.strip()
            if not line:
                continue
            n_in += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                # If a line is broken, skip it (you can change this behavior if needed)
                continue

            if not isinstance(rec, dict):
                continue

            opt_field, options = extract_options(rec)
            qid = extract_id(rec, idx)
            question = build_question(rec, opt_field, options)
            answer = resolve_answer(rec, options)

            out = {
                "id": qid,
                "question": question,
                "answer": answer,
            }
            fout.write(json.dumps(out, ensure_ascii=False) + "\n")
            n_out += 1

    print(f"Done. Read {n_in} lines, wrote {n_out} samples to: {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert JSONL dataset to {id, question, answer} JSONL.")
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    convert_jsonl(args.input, args.output)


if __name__ == "__main__":
    main()
