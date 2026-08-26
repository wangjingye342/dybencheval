#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Convert a JSONL dataset into a training-friendly format:
Each output line: {"id": ..., "question": "...", "answer": "..."}

Default mapping (fits your dataset):
- question: uses field "article"
- answer: uses field "abstract"
- id: uses an existing id field if provided, otherwise uses an auto-increment index.

Usage examples:
1) Default (article -> question, abstract -> answer):
   python convert_jsonl.py --input input.jsonl --output output.jsonl

2) Custom mapping:
   python convert_jsonl.py --input in.jsonl --output out.jsonl \
       --question_fields title,article --answer_field abstract --id_field paper_id

3) Change instruction/prefix text:
   python convert_jsonl.py --input in.jsonl --output out.jsonl \
       --question_prefix "Please read the following content and answer:\n"
"""

import argparse
import json
import os
from typing import Any, Dict, List, Optional


def safe_str(x: Any) -> str:
    """Convert a value to a clean string."""
    if x is None:
        return ""
    if isinstance(x, str):
        return x.strip()
    # For list/dict/number/bool etc.
    return str(x).strip()


def build_question(
    record: Dict[str, Any],
    question_fields: List[str],
    question_prefix: str,
    add_field_labels: bool,
) -> str:
    """
    Build 'question' by concatenating the specified fields.

    If add_field_labels is True, format as:
        <prefix>
        [field1]: ...
        [field2]: ...
    Otherwise, join the field contents with two newlines.
    """
    parts: List[str] = []

    for f in question_fields:
        val = safe_str(record.get(f))
        if not val:
            continue
        if add_field_labels:
            parts.append(f"[{f}]: {val}")
        else:
            parts.append(val)

    body = "\n\n".join(parts).strip()
    return (question_prefix or "") + body


def convert_jsonl(
    input_path: str,
    output_path: str,
    question_fields: List[str],
    answer_field: str,
    id_field: Optional[str],
    question_prefix: str,
    add_field_labels: bool,
    skip_if_no_answer: bool,
) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    out_count = 0
    in_count = 0

    with open(input_path, "r", encoding="utf-8") as fin, open(
        output_path, "w", encoding="utf-8"
    ) as fout:
        for _, line in enumerate(fin):
            line = line.strip()
            if not line:
                continue

            in_count += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                # If a line is malformed, skip it (or raise an error if you prefer)
                continue

            answer = safe_str(record.get(answer_field))
            if skip_if_no_answer and not answer:
                continue

            question = build_question(
                record=record,
                question_fields=question_fields,
                question_prefix=question_prefix,
                add_field_labels=add_field_labels,
            ).strip()

            # ID logic: use record[id_field] if provided and present; otherwise use sequential index
            if id_field and (id_field in record) and safe_str(record.get(id_field)):
                sample_id = safe_str(record.get(id_field))
            else:
                sample_id = str(out_count)

            new_obj = {
                "id": sample_id,
                "question": question,
                "answer": answer,
            }
            fout.write(json.dumps(new_obj, ensure_ascii=False) + "\n")
            out_count += 1

    print(f"Done. Read {in_count} lines, wrote {out_count} samples to: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a JSONL dataset to id/question/answer JSONL."
    )
    parser.add_argument("--input", required=True, help="Path to the input JSONL file.")
    parser.add_argument("--output", required=True, help="Path to the output JSONL file.")

    # Default mapping for your dataset
    parser.add_argument(
        "--question_fields",
        default="article",
        help="Comma-separated fields used to build 'question'. Default: article",
    )
    parser.add_argument(
        "--answer_field",
        default="abstract",
        help="Field used as 'answer'. Default: abstract",
    )
    parser.add_argument(
        "--id_field",
        default="",
        help="Optional field name used as 'id'. If empty or missing, an auto id is used.",
    )

    parser.add_argument(
        "--question_prefix",
        default="Please summarize the following article:\n",
        help="Prefix text prepended before the question content.",
    )
    parser.add_argument(
        "--add_field_labels",
        action="store_true",
        help="If set, prefix each field in the question with [field_name]:",
    )
    parser.add_argument(
        "--skip_if_no_answer",
        action="store_true",
        help="If set, skip samples with an empty answer.",
    )

    args = parser.parse_args()

    question_fields = [f.strip() for f in args.question_fields.split(",") if f.strip()]
    if not question_fields:
        raise ValueError("question_fields is empty. Provide at least one field name.")

    id_field = args.id_field.strip() or None

    convert_jsonl(
        input_path=args.input,
        output_path=args.output,
        question_fields=question_fields,
        answer_field=args.answer_field.strip(),
        id_field=id_field,
        question_prefix=args.question_prefix,
        add_field_labels=args.add_field_labels,
        skip_if_no_answer=args.skip_if_no_answer,
    )


if __name__ == "__main__":
    main()
