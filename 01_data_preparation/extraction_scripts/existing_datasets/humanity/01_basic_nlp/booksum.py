# -*- coding: utf-8 -*-
"""
Convert a JSONL dataset into training format:
{"id": "...", "question": "...", "answer": "..."}

This version is tailored for your new dataset fields (observed):
- chapter (long original text)
- summary_text (reference summary)
- summary_analysis (optional analysis)

Default behavior:
- question: includes useful metadata + full chapter text
- answer: includes summary_text (and summary_analysis if present)

Run:
  python convert_to_qa_v2.py --input input.jsonl --output output.jsonl

You can customize:
  --question-template "..."
  --answer-template "..."
  --id-prefix sample_
  --start-id 1
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
        # Keep JSON as compact string if needed
        return json.dumps(v, ensure_ascii=False)
    return str(v)


class SafeDict(dict):
    """Return empty string for missing keys in .format_map()."""
    def __missing__(self, key):
        return ""


def render_template(template: str, item: Dict[str, Any]) -> str:
    safe_item = {k: norm_value(v) for k, v in item.items()}
    text = template.format_map(SafeDict(safe_item))
    # Clean up excessive trailing spaces
    return text.strip()


def postprocess_answer(ans: str) -> str:
    """Remove empty sections like 'Analysis:' if analysis is missing."""
    lines = [ln.rstrip() for ln in ans.splitlines()]
    # Drop fully empty leading/trailing lines
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines).strip()


def convert_jsonl(
    input_path: str,
    output_path: str,
    question_template: str,
    answer_template: str,
    id_prefix: str,
    start_id: int,
    require_nonempty_answer: bool = True,
    require_nonempty_question: bool = True,
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
            answer = postprocess_answer(answer)

            if require_nonempty_question and not question:
                skipped += 1
                continue
            if require_nonempty_answer and not answer:
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
    parser = argparse.ArgumentParser(description="Convert JSONL to {id, question, answer} JSONL (English templates).")
    parser.add_argument("--input", required=True, help="Input JSONL path")
    parser.add_argument("--output", required=True, help="Output JSONL path")

    # Default templates for your dataset (English)
    parser.add_argument(
        "--question-template",
        default=(
            "Source: {source}\n"
            "Book ID: {book_id}\n"
            "Chapter: {summary_name}\n"
            "Chapter Path: {chapter_path}\n"
            "\n"
            "Text:\n"
            "{chapter}"
        ),
        help="Question template (English). Use {field} placeholders."
    )

    parser.add_argument(
        "--answer-template",
        default=(
            "Summary:\n"
            "{summary_text}\n"
            "\n"
            "Analysis:\n"
            "{summary_analysis}"
        ),
        help="Answer template. Use {field} placeholders."
    )

    parser.add_argument("--id-prefix", default="sample_", help="Generated id prefix (default: sample_)")
    parser.add_argument("--start-id", type=int, default=1, help="Starting integer for id suffix (default: 1)")
    parser.add_argument(
        "--allow-empty-analysis",
        action="store_true",
        help="Keep 'Analysis:' section even if summary_analysis is empty (default: drop empties by trimming)."
    )

    args = parser.parse_args()

    convert_jsonl(
        input_path=args.input,
        output_path=args.output,
        question_template=args.question_template,
        answer_template=args.answer_template,
        id_prefix=args.id_prefix,
        start_id=args.start_id,
        require_nonempty_answer=True,
        require_nonempty_question=True,
    )


if __name__ == "__main__":
    main()
