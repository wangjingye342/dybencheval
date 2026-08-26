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


def _extract_answer_text(answers: Any, mode: str) -> Optional[str]:
    """
    mode:
      - first: 取 answers[0]
      - join:  多答案用 ' ||| ' 拼接
    """
    if isinstance(answers, list) and answers:
        strs = []
        for a in answers:
            if isinstance(a, str) and a.strip():
                strs.append(a.strip())
            elif a is not None:
                s = _as_str(a).strip()
                if s:
                    strs.append(s)
        if not strs:
            return None
        if mode == "join":
            return " ||| ".join(strs)
        return strs[0]
    if isinstance(answers, str) and answers.strip():
        return answers.strip()
    return None


def _format_spans(labels: Any, context: str, max_spans: int = 6) -> str:
    """
    labels: list[{"start":[int], "end":[int]}]
    生成一个紧凑的 span 展示，帮助模型对齐（可选）。
    """
    if not isinstance(labels, list) or not labels:
        return ""
    items: List[str] = []
    for lab in labels[:max_spans]:
        if not isinstance(lab, dict):
            continue
        starts = lab.get("start")
        ends = lab.get("end")
        if not (isinstance(starts, list) and isinstance(ends, list) and starts and ends):
            continue
        s, e = starts[0], ends[0]
        if not (isinstance(s, int) and isinstance(e, int)):
            continue
        if 0 <= s <= e <= len(context):
            snippet = context[s:e]
            snippet = snippet.replace("\n", " ").strip()
            items.append(f"- [{s}, {e}] {snippet}")
        else:
            items.append(f"- [{_as_str(s)}, {_as_str(e)}]")

    if not items:
        return ""
    return "Answer spans (char offsets):\n" + "\n".join(items) + "\n\n"


def build_qa(example: Dict[str, Any], line_idx: int, answer_mode: str, include_spans: bool) -> Optional[Dict[str, str]]:
    context = example.get("context")
    question = example.get("question")
    answers = example.get("answers")
    key = example.get("key")
    labels = example.get("labels")

    if not isinstance(context, str) or not isinstance(question, str):
        return None

    ans_text = _extract_answer_text(answers, mode=answer_mode)
    if ans_text is None:
        return None

    out_id = str(key) if key is not None else str(line_idx)

    spans_block = _format_spans(labels, context) if include_spans else ""

    q = (
        "Answer the question based on the given context.\n\n"
        + spans_block
        + "Context:\n"
        + context.strip()
        + "\n\nQuestion:\n"
        + question.strip()
        + "\n\nReturn only the final answer."
    )

    return {"id": out_id, "question": q, "answer": ans_text}


def convert_jsonl(input_path: str, output_path: str, answer_mode: str, include_spans: bool) -> None:
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

            qa = build_qa(ex, i, answer_mode=answer_mode, include_spans=include_spans)
            if qa is None:
                skipped += 1
                continue

            fout.write(json.dumps(qa, ensure_ascii=False) + "\n")
            written += 1

    print(f"Done. Written={written}, Skipped={skipped}, TotalLines={total}")
    print(f"Output saved to: {output_path}")
    if written == 0:
        print("WARNING: Written=0. Likely schema mismatch or all lines failed parsing.")


def main():
    parser = argparse.ArgumentParser(description="Convert extractive QA JSONL into {id, question, answer} JSONL.")
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    parser.add_argument(
        "--answer_mode",
        choices=["first", "join"],
        default="first",
        help="first: use answers[0]. join: join multiple answers with ' ||| '.",
    )
    parser.add_argument(
        "--include_spans",
        action="store_true",
        help="Include char-offset answer spans (labels) in the question.",
    )
    args = parser.parse_args()

    convert_jsonl(args.input, args.output, answer_mode=args.answer_mode, include_spans=args.include_spans)


if __name__ == "__main__":
    main()
