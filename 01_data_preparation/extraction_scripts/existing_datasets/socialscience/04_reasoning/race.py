#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
from typing import Any, Dict, List, Optional


LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _as_str(x: Any) -> str:
    if isinstance(x, str):
        return x
    return json.dumps(x, ensure_ascii=False)


def _answer_to_index(ans: Any, n: int) -> Optional[int]:
    """
    兼容 answer 格式：
    - "A"/"B"/"C"/"D" -> 0/1/2/3
    - "0"/"1"/... 或 int -> 直接当索引（同时兼容 1-based）
    - 也可能直接给了答案文本（这种返回 None，外部再处理）
    """
    if isinstance(ans, str):
        s = ans.strip()
        if not s:
            return None

        # 字母答案
        if len(s) == 1 and s.upper() in LETTERS[:n]:
            return LETTERS.index(s.upper())

        # 数字索引（字符串）
        if s.isdigit():
            v = int(s)
            if 0 <= v < n:
                return v
            if 1 <= v <= n:
                return v - 1
            return None

        return None

    if isinstance(ans, int) and not isinstance(ans, bool):
        if 0 <= ans < n:
            return ans
        if 1 <= ans <= n:
            return ans - 1
        return None

    return None


def build_qa(example: Dict[str, Any], line_idx: int) -> Optional[Dict[str, str]]:
    article = example.get("article")
    question = example.get("question")
    options = example.get("options")
    ans = example.get("answer")

    if not isinstance(article, str) or not isinstance(question, str) or not isinstance(options, list) or not options:
        return None

    # 选项转字符串
    opt_texts: List[str] = []
    for o in options:
        s = _as_str(o).strip()
        opt_texts.append(s)

    # 生成答案文本
    ans_idx = _answer_to_index(ans, len(opt_texts))
    if ans_idx is not None:
        answer_text = opt_texts[ans_idx]
    else:
        # 若 answer 本身就是文本（少数数据会这样），就直接用
        if isinstance(ans, str) and ans.strip():
            answer_text = ans.strip()
        else:
            return None

    # 组装 options 展示：A. ... / B. ...
    option_lines = []
    for i, t in enumerate(opt_texts):
        label = LETTERS[i] if i < len(LETTERS) else str(i)
        option_lines.append(f"{label}. {t}")

    q = (
        "Answer the multiple-choice question based on the article.\n\n"
        f"Article:\n{article.strip()}\n\n"
        f"Question:\n{question.strip()}\n\n"
        "Options:\n" + "\n".join(option_lines) + "\n\n"
        "Return only the final answer."
    )

    ex_id = example.get("example_id")
    out_id = str(ex_id) if ex_id is not None else str(line_idx)

    return {"id": out_id, "question": q, "answer": answer_text}


def convert_jsonl(input_path: str, output_path: str) -> None:
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

            qa = build_qa(ex, i)
            if qa is None:
                skipped += 1
                continue

            fout.write(json.dumps(qa, ensure_ascii=False) + "\n")
            written += 1

    print(f"Done. Written={written}, Skipped={skipped}, TotalLines={total}")
    print(f"Output saved to: {output_path}")
    if written == 0:
        print("WARNING: Written=0. Likely schema mismatch or parsing issues.")


def main():
    parser = argparse.ArgumentParser(
        description="Convert article/question/options/answer JSONL into training JSONL with {id, question, answer}."
    )
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    args = parser.parse_args()

    convert_jsonl(args.input, args.output)


if __name__ == "__main__":
    main()
