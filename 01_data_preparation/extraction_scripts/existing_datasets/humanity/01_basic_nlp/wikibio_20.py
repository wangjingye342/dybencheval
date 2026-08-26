# -*- coding: utf-8 -*-
"""
Convert a JSONL dataset with fields:
  - prompt
  - input
  - output
into training format JSONL:
  {"id": "...", "question": "...", "answer": "..."}

Default:
- question template (English):
    Instruction: {prompt}

    Input:
    {input}
- answer: {output}

Run:
  python convert_prompt_input_output_to_qa.py --input input.jsonl --output output.jsonl

Example (using your uploaded file path):
  python convert_prompt_input_output_to_qa.py \
    --input /mnt/data/711d6e8a-7ed0-413a-8338-cf79d8eada51.jsonl \
    --output output_dataset3.jsonl
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


def clean_question(q: str) -> str:
    # Remove excessive blank lines
    lines = [ln.rstrip() for ln in q.splitlines()]
    # Trim leading/trailing empty lines
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    # Collapse multiple consecutive empty lines to max 2
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


def convert_jsonl(
    input_path: str,
    output_path: str,
    question_template: str,
    answer_template: str,
    id_prefix: str,
    start_id: int,
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
            answer = render_template(answer_template, item)

            question = clean_question(question)
            answer = answer.strip()

            # Require both question and answer
            if not question or not answer:
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
        description="Convert JSONL (prompt/input/output) to {id, question, answer} JSONL."
    )
    parser.add_argument("--input", required=True, help="Input JSONL path")
    parser.add_argument("--output", required=True, help="Output JSONL path")

    # English default templates for this dataset
    parser.add_argument(
        "--question-template",
        default=(
            "Instruction: {prompt}\n\n"
            "Input:\n"
            "{input}"
        ),
        help="Question template (English). Use {prompt}, {input}, etc."
    )
    parser.add_argument(
        "--answer-template",
        default="{output}",
        help="Answer template. Use {output} etc."
    )

    parser.add_argument("--id-prefix", default="sample_", help="Generated id prefix (default: sample_)")
    parser.add_argument("--start-id", type=int, default=1, help="Starting integer for id suffix (default: 1)")

    args = parser.parse_args()

    convert_jsonl(
        input_path=args.input,
        output_path=args.output,
        question_template=args.question_template,
        answer_template=args.answer_template,
        id_prefix=args.id_prefix,
        start_id=args.start_id,
    )


if __name__ == "__main__":
    main()
