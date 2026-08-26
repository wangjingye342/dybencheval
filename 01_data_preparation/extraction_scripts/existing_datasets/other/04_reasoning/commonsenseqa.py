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


def build_qa(example: Dict[str, Any], line_idx: int) -> Optional[Dict[str, str]]:
    qid = example.get("id")
    question = example.get("question")
    concept = example.get("question_concept")
    choices = example.get("choices")
    answer_key = example.get("answerKey")

    if not isinstance(question, str) or not isinstance(choices, dict) or not isinstance(answer_key, str):
        return None

    labels = choices.get("label")
    texts = choices.get("text")

    if not isinstance(labels, list) or not isinstance(texts, list) or len(labels) != len(texts) or len(labels) == 0:
        return None

    # 找到正确答案文本
    answer_key = answer_key.strip()
    try:
        idx = labels.index(answer_key)
    except ValueError:
        return None

    answer_text = texts[idx]
    if not isinstance(answer_text, str):
        answer_text = _as_str(answer_text)

    # 拼 question
    option_lines: List[str] = []
    for lab, txt in zip(labels, texts):
        option_lines.append(f"{_as_str(lab)}. {_as_str(txt)}")

    concept_block = f"Concept: {_as_str(concept)}\n\n" if concept is not None else ""
    prompt = (
        "Answer the following multiple-choice question.\n\n"
        + concept_block
        + f"Question:\n{question.strip()}\n\n"
        + "Options:\n"
        + "\n".join(option_lines)
    )

    out_id = str(qid) if qid is not None else str(line_idx)
    return {"id": out_id, "question": prompt, "answer": answer_text.strip()}


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
    parser = argparse.ArgumentParser(description="Convert JSONL MCQ dataset into {id, question, answer} JSONL.")
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    args = parser.parse_args()
    convert_jsonl(args.input, args.output)


if __name__ == "__main__":
    main()
