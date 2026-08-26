# -*- coding: utf-8 -*-
"""
Convert JSONL with fields like:
  Type, Category, Question, Best Answer, Correct Answers, Incorrect Answers, Source
into training format JSONL:
  {"id": "...", "question": "...", "answer": "..."}

Default:
- question (English): includes Type/Category/Source + the Question
- answer: Best Answer (fallback to Correct Answers if Best Answer is empty)

Run:
  python convert_benchmark_qa_to_training.py --input input.jsonl --output output.jsonl

Example (your uploaded file path):
  python convert_benchmark_qa_to_training.py \
    --input /mnt/data/32ec897f-cf62-4f0e-947a-7f6592e4fe9e.jsonl \
    --output output_dataset6.jsonl
"""

import argparse
import json
import math
from typing import Any, Dict


def is_nan(x: Any) -> bool:
    return isinstance(x, float) and math.isnan(x)


def norm_value(v: Any) -> str:
    """Normalize values to safe string (NaN/None -> '')."""
    if v is None or is_nan(v):
        return ""
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


class SafeDict(dict):
    """Return empty string for missing keys in .format_map()."""
    def __missing__(self, key):
        return ""


def render_template(template: str, item: Dict[str, Any]) -> str:
    safe_item = {k: norm_value(v) for k, v in item.items()}
    return template.format_map(SafeDict(safe_item)).strip()


def clean_text(s: str) -> str:
    """Trim and collapse excessive blank lines."""
    lines = [ln.rstrip() for ln in s.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    out = []
    empty_run = 0
    for ln in lines:
        if ln.strip():
            empty_run = 0
            out.append(ln)
        else:
            empty_run += 1
            if empty_run <= 2:
                out.append("")
    return "\n".join(out).strip()


def pick_answer(item: Dict[str, Any], primary: str, fallback: str) -> str:
    a1 = norm_value(item.get(primary, "")).strip()
    if a1:
        return a1
    a2 = norm_value(item.get(fallback, "")).strip()
    return a2


def convert_jsonl(
    input_path: str,
    output_path: str,
    question_template: str,
    answer_primary_field: str,
    answer_fallback_field: str,
    id_prefix: str,
    start_id: int,
    require_nonempty: bool = True,
) -> None:
    written = 0
    skipped = 0

    with open(input_path, "r", encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout:
        for line_no, line in enumerate(fin, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue

            question = render_template(question_template, item)
            answer = pick_answer(item, answer_primary_field, answer_fallback_field)

            question = clean_text(question)
            answer = clean_text(answer)

            if require_nonempty and (not question or not answer):
                skipped += 1
                continue

            new_id = f"{id_prefix}{start_id + written}"
            out_obj = {"id": new_id, "question": question, "answer": answer}
            fout.write(json.dumps(out_obj, ensure_ascii=False) + "\n")
            written += 1

    print(f"Done. Wrote {written} records to: {output_path}")
    if skipped:
        print(f"Skipped {skipped} lines (empty/invalid/missing required fields).")


def main():
    parser = argparse.ArgumentParser(
        description="Convert JSONL (Type/Category/Question/Best Answer/Correct Answers/...) to {id, question, answer} JSONL."
    )
    parser.add_argument("--input", required=True, help="Input JSONL path")
    parser.add_argument("--output", required=True, help="Output JSONL path")

    # English default template: include all useful info
    parser.add_argument(
        "--question-template",
        default=(
            "Type: {Type}\n"
            "Category: {Category}\n"
            "Source: {Source}\n"
            "\n"
            "Question:\n"
            "{Question}"
        ),
        help="Question template (English). Use {Type}, {Category}, {Source}, {Question}, etc."
    )

    parser.add_argument(
        "--answer-primary-field",
        default="Best Answer",
        help='Primary answer field (default: "Best Answer")'
    )
    parser.add_argument(
        "--answer-fallback-field",
        default="Correct Answers",
        help='Fallback answer field if primary is empty (default: "Correct Answers")'
    )

    parser.add_argument("--id-prefix", default="sample_", help="Generated id prefix (default: sample_)")
    parser.add_argument("--start-id", type=int, default=1, help="Starting integer for id suffix (default: 1)")

    args = parser.parse_args()

    convert_jsonl(
        input_path=args.input,
        output_path=args.output,
        question_template=args.question_template,
        answer_primary_field=args.answer_primary_field,
        answer_fallback_field=args.answer_fallback_field,
        id_prefix=args.id_prefix,
        start_id=args.start_id,
        require_nonempty=True,
    )


if __name__ == "__main__":
    main()
