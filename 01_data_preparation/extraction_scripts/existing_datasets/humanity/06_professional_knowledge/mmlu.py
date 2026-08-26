#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
from typing import Any, Dict, List, Optional


def _as_str(x: Any) -> str:
    """把任意对象稳定转成字符串（保留中文）"""
    if isinstance(x, str):
        return x
    return json.dumps(x, ensure_ascii=False)


def build_qa(example: Dict[str, Any], idx: int) -> Optional[Dict[str, str]]:
    """
    自动识别样本结构并转换为 {id, question, answer}
    支持：
      1) context + endings + label
      2) question + choices + answer (+ subject)
    """
    # -------- 结构 A：context/endings/label --------
    if "context" in example and "endings" in example and "label" in example:
        context = example.get("context")
        endings = example.get("endings")
        label = example.get("label")

        if not isinstance(context, str) or not isinstance(endings, list) or not isinstance(label, int):
            return None
        if not (0 <= label < len(endings)):
            return None

        option_lines = [f"{i}. {_as_str(opt)}" for i, opt in enumerate(endings)]
        question = (
            "Given the context, choose the correct ending.\n\n"
            f"Context:\n{context}\n\n"
            "Options:\n" + "\n".join(option_lines)
        )
        answer = _as_str(endings[label])

        return {"id": str(idx), "question": question, "answer": answer}

    # -------- 结构 B：question/choices/answer(+subject) --------
    if "question" in example and "choices" in example and "answer" in example:
        q = example.get("question")
        choices = example.get("choices")
        ans = example.get("answer")  # 通常是索引 int
        subject = example.get("subject")  # 可选

        if not isinstance(q, str) or not isinstance(choices, list):
            return None

        # answer 可能是索引，也可能是文本（做兼容）
        answer_text: Optional[str] = None
        if isinstance(ans, int):
            if not (0 <= ans < len(choices)):
                return None
            answer_text = _as_str(choices[ans])
        elif isinstance(ans, str):
            # 若直接给了正确答案文本
            answer_text = ans
        else:
            return None

        option_lines = [f"{i}. {_as_str(opt)}" for i, opt in enumerate(choices)]

        # 把 subject 也作为有用信息拼进去（如果存在）
        subject_block = f"Subject: {_as_str(subject)}\n\n" if subject is not None else ""

        question = (
            subject_block
            + "Answer the following multiple-choice question.\n\n"
            f"Question:\n{q}\n\n"
            "Options:\n" + "\n".join(option_lines)
        )

        return {"id": str(idx), "question": question, "answer": answer_text}

    # -------- 未识别结构 --------
    return None


def convert_jsonl(input_path: str, output_path: str) -> None:
    written = 0
    skipped = 0

    with open(input_path, "r", encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout:
        for idx, line in enumerate(fin):
            line = line.strip()
            if not line:
                skipped += 1
                continue

            try:
                example = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue

            qa = build_qa(example, idx)
            if qa is None:
                skipped += 1
                continue

            fout.write(json.dumps(qa, ensure_ascii=False) + "\n")
            written += 1

    print(f"Done. Written: {written}, Skipped: {skipped}")
    print(f"Output saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert JSONL dataset into training JSONL with {id, question, answer}."
    )
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    args = parser.parse_args()

    convert_jsonl(args.input, args.output)


if __name__ == "__main__":
    main()
