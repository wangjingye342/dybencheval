#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import re
from typing import Any, Dict, List, Optional


def _as_str(x: Any) -> str:
    if isinstance(x, str):
        return x
    return json.dumps(x, ensure_ascii=False)


def _strip_think(text: str) -> str:
    """
    去掉 <think>...</think> 块（常用于推理/草稿），保留最终回答。
    如果你希望保留推理，把 convert_jsonl() 里 strip_think=False 即可。
    """
    # 非贪婪匹配，跨行
    return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()


def _format_prompt(prompt: Any) -> Optional[str]:
    """
    prompt 通常是 [{"role":"user","content":"..."}, ...]
    也兼容直接给字符串。
    """
    if isinstance(prompt, str):
        return prompt.strip()

    if not isinstance(prompt, list) or not prompt:
        return None

    lines: List[str] = []
    for msg in prompt:
        if isinstance(msg, dict):
            role = msg.get("role")
            content = msg.get("content")
            if isinstance(content, str):
                r = str(role) if role is not None else "unknown"
                lines.append(f"{r}: {content}")
            else:
                # content 非字符串也尽量保留
                r = str(role) if role is not None else "unknown"
                lines.append(f"{r}: {_as_str(content)}")
        else:
            lines.append(_as_str(msg))

    return "\n".join(lines).strip()


# ------------------------- Schema H: prompt/solution (chat style) -------------------------
def _convert_prompt_solution(example: Dict[str, Any], fallback_id: str, strip_think: bool = True) -> Optional[Dict[str, str]]:
    prompt = example.get("prompt")
    solution = example.get("solution")

    if solution is None:
        return None
    if not isinstance(solution, str):
        solution = _as_str(solution)

    prompt_text = _format_prompt(prompt)
    if prompt_text is None:
        return None

    # 附加元信息（可按需删改）
    data_source = example.get("data_source")
    ability = example.get("ability")
    extra_info = example.get("extra_info") if isinstance(example.get("extra_info"), dict) else {}

    domain = extra_info.get("domain") if isinstance(extra_info, dict) else None
    chinese = extra_info.get("chinese") if isinstance(extra_info, dict) else None

    meta_lines: List[str] = []
    if data_source is not None:
        meta_lines.append(f"- data_source: {_as_str(data_source)}")
    if ability is not None:
        meta_lines.append(f"- ability: {_as_str(ability)}")
    if domain is not None:
        meta_lines.append(f"- domain: {_as_str(domain)}")
    if chinese is not None:
        meta_lines.append(f"- chinese: {_as_str(chinese)}")

    meta_block = ""
    if meta_lines:
        meta_block = "Meta:\n" + "\n".join(meta_lines) + "\n\n"

    question = (
        "Please respond to the user's request.\n\n"
        + meta_block
        + "Conversation:\n"
        + prompt_text
    )

    answer = _strip_think(solution) if strip_think else solution.strip()
    return {"id": fallback_id, "question": question, "answer": answer}


def convert_jsonl(input_path: str, output_path: str, strip_think: bool = True) -> None:
    written, skipped = 0, 0

    with open(input_path, "r", encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout:
        for line_idx, line in enumerate(fin):
            line = line.strip()
            if not line:
                skipped += 1
                continue

            try:
                example = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue

            # id：优先 extra_info.index，其次 example.id，其次行号
            fallback_id = str(line_idx)
            if isinstance(example, dict):
                extra = example.get("extra_info")
                if isinstance(extra, dict) and extra.get("index") is not None:
                    fallback_id = str(extra["index"])
                elif example.get("id") is not None:
                    fallback_id = str(example["id"])

            qa = None
            if isinstance(example, dict) and ("prompt" in example and "solution" in example):
                qa = _convert_prompt_solution(example, fallback_id, strip_think=strip_think)

            if qa is None:
                skipped += 1
                continue

            fout.write(json.dumps(qa, ensure_ascii=False) + "\n")
            written += 1

    print(f"Done. Written: {written}, Skipped: {skipped}")
    print(f"Output saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Convert JSONL into training JSONL with {id, question, answer}.")
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    parser.add_argument(
        "--keep_think",
        action="store_true",
        help="Keep <think>...</think> in solution (default: strip it)."
    )
    args = parser.parse_args()

    convert_jsonl(args.input, args.output, strip_think=(not args.keep_think))


if __name__ == "__main__":
    main()
