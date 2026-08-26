# -*- coding: utf-8 -*-
"""
Convert JSONL with fields:
  - context (str)
  - query (str)
  - options (list[str])
  - correct_option (int, maybe 0-based or 1-based)
into training format JSONL:
  {"id": "...", "question": "...", "answer": "..."}

Default question (English):
Context:
{context}

Question:
{query}

Options:
A. ...
B. ...
C. ...
D. ...

Default answer (English):
Correct option: D. <option text>

Run:
  python convert_mcq_to_training.py --input input.jsonl --output output.jsonl

Example (your uploaded file path):
  python convert_mcq_to_training.py \
    --input /mnt/data/4f02b399-f739-4a57-b53a-10880b88fdcf.jsonl \
    --output output_dataset7.jsonl
"""

import argparse
import json
import math
from typing import Any, Dict, List, Optional


def is_nan(x: Any) -> bool:
    return isinstance(x, float) and math.isnan(x)


def norm_str(v: Any) -> str:
    if v is None or is_nan(v):
        return ""
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def clean_text(s: str) -> str:
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


def option_label(i: int) -> str:
    # 0->A, 1->B, ...
    return chr(ord("A") + i)


def format_options(options: List[Any]) -> str:
    lines = []
    for i, opt in enumerate(options):
        opt_text = clean_text(norm_str(opt))
        lines.append(f"{option_label(i)}. {opt_text}")
    return "\n".join(lines).strip()


def resolve_correct_index(correct_option: Any, n_options: int) -> Optional[int]:
    """
    Handle both 0-based and 1-based indices.
    - If correct_option is int and in [0, n_options-1], treat as 0-based.
    - Else if in [1, n_options], treat as 1-based and convert to 0-based.
    """
    try:
        k = int(correct_option)
    except Exception:
        return None

    if 0 <= k < n_options:
        return k
    if 1 <= k <= n_options:
        return k - 1
    return None


def build_question(context: str, query: str, options_block: str, template: str) -> str:
    return clean_text(
        template.format(
            context=context,
            query=query,
            options=options_block
        )
    )


def build_answer(options: List[Any], correct_idx: Optional[int], template: str) -> str:
    if correct_idx is None or correct_idx < 0 or correct_idx >= len(options):
        return ""

    label = option_label(correct_idx)
    opt_text = clean_text(norm_str(options[correct_idx]))
    return clean_text(template.format(label=label, option=opt_text, index=correct_idx))


def convert_jsonl(
    input_path: str,
    output_path: str,
    id_prefix: str,
    start_id: int,
    question_template: str,
    answer_template: str,
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

            context = clean_text(norm_str(item.get("context", "")))
            query = clean_text(norm_str(item.get("query", "")))
            options = item.get("options", [])

            if not isinstance(options, list):
                options = []

            options_block = format_options(options)
            correct_idx = resolve_correct_index(item.get("correct_option", None), len(options))

            question = build_question(context, query, options_block, question_template)
            answer = build_answer(options, correct_idx, answer_template)

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
    parser = argparse.ArgumentParser(description="Convert MCQ JSONL to {id, question, answer} JSONL (English).")
    parser.add_argument("--input", required=True, help="Input JSONL path")
    parser.add_argument("--output", required=True, help="Output JSONL path")

    parser.add_argument("--id-prefix", default="sample_", help="Generated id prefix (default: sample_)")
    parser.add_argument("--start-id", type=int, default=1, help="Starting integer for id suffix (default: 1)")

    parser.add_argument(
        "--question-template",
        default=(
            "Context:\n{context}\n\n"
            "Question:\n{query}\n\n"
            "Options:\n{options}"
        ),
        help="English question template. Available placeholders: {context}, {query}, {options}"
    )

    parser.add_argument(
        "--answer-template",
        default="Correct option: {label}. {option}",
        help="English answer template. Available placeholders: {label}, {option}, {index}"
    )

    args = parser.parse_args()

    convert_jsonl(
        input_path=args.input,
        output_path=args.output,
        id_prefix=args.id_prefix,
        start_id=args.start_id,
        question_template=args.question_template,
        answer_template=args.answer_template,
        require_nonempty=True,
    )


if __name__ == "__main__":
    main()
