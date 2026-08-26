# -*- coding: utf-8 -*-
"""
Convert a JSONL dataset into training format:
{"id": "...", "question": "...", "answer": "..."}

Default mapping for your file (based on observed fields):
- question = combines "title" + "text"
- answer   = "summary"

Usage examples:
1) Basic:
   python convert_to_qa.py --input input.jsonl --output output.jsonl

2) Customize which fields go into question/answer:
   python convert_to_qa.py --input input.jsonl --output output.jsonl \
       --question-fields title text --answer-field summary

3) Customize question template:
   python convert_to_qa.py --input input.jsonl --output output.jsonl \
       --question-template "标题：{title}\n\n正文：{text}\n"
"""

import argparse
import json
from typing import Dict, Any, List


def build_question(item: Dict[str, Any], fields: List[str], template: str) -> str:
    """
    Build the question text from item.
    If template is provided, it will be formatted with item keys.
    Otherwise, fields are concatenated as "field: value".
    """
    if template:
        # Missing keys become empty string to avoid KeyError
        safe_item = {k: ("" if item.get(k) is None else str(item.get(k))) for k in item.keys()}
        # Also allow formatting even if some keys don't exist in the record
        class SafeDict(dict):
            def __missing__(self, key):
                return ""
        return template.format_map(SafeDict(safe_item)).strip()

    parts = []
    for f in fields:
        v = item.get(f, "")
        if v is None:
            v = ""
        v = str(v).strip()
        if v:
            parts.append(f"{f}: {v}")
    return "\n\n".join(parts).strip()


def build_answer(item: Dict[str, Any], answer_field: str) -> str:
    v = item.get(answer_field, "")
    if v is None:
        v = ""
    return str(v).strip()


def convert_jsonl(input_path: str,
                  output_path: str,
                  question_fields: List[str],
                  answer_field: str,
                  id_prefix: str,
                  start_id: int,
                  question_template: str) -> None:
    out_count = 0
    with open(input_path, "r", encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout:
        for idx, line in enumerate(fin):
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                # Skip broken lines
                continue

            question = build_question(item, question_fields, question_template)
            answer = build_answer(item, answer_field)

            # Only keep records that have both question and answer
            if not question or not answer:
                continue

            new_id = f"{id_prefix}{start_id + out_count}"

            out_obj = {
                "id": new_id,
                "question": question,
                "answer": answer
            }
            fout.write(json.dumps(out_obj, ensure_ascii=False) + "\n")
            out_count += 1

    print(f"Done. Wrote {out_count} records to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Convert JSONL to {id, question, answer} JSONL.")
    parser.add_argument("--input", required=True, help="Input JSONL filename/path")
    parser.add_argument("--output", required=True, help="Output JSONL filename/path")

    # Defaults match your dataset's observed keys: title/text/summary
    parser.add_argument("--question-fields", nargs="+", default=["title", "text"],
                        help="Fields to include in question when no template is used (default: title text)")
    parser.add_argument("--answer-field", default="summary",
                        help="Field to use as answer (default: summary)")

    parser.add_argument("--question-template", default="Title：{title}\n\nContent：{text}",
                        help="Optional template to build question. Use {field} placeholders. "
                             "Set to empty string to disable templating and use --question-fields instead.")

    parser.add_argument("--id-prefix", default="sample_",
                        help="Prefix for generated id (default: sample_)")
    parser.add_argument("--start-id", type=int, default=1,
                        help="Starting integer for id suffix (default: 1)")

    args = parser.parse_args()

    convert_jsonl(
        input_path=args.input,
        output_path=args.output,
        question_fields=args.question_fields,
        answer_field=args.answer_field,
        id_prefix=args.id_prefix,
        start_id=args.start_id,
        question_template=args.question_template.strip()
    )


if __name__ == "__main__":
    main()
