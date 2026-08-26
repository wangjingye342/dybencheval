#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
from typing import Any, Dict, List, Optional


def build_qa(example: Dict[str, Any], idx: int) -> Optional[Dict[str, str]]:
    """
    将一条原始样本转换为 {id, question, answer}。
    你可以在这里自由改 question 的组织方式，或改 answer 的内容。
    """
    context = example.get("context")
    endings = example.get("endings")
    label = example.get("label")

    # 基本校验
    if not isinstance(context, str) or not isinstance(endings, list) or not isinstance(label, int):
        return None
    if not (0 <= label < len(endings)):
        return None

    # 组织 question：给模型的有用信息（上下文 + 备选项）
    # 你可按需要修改模板，例如增加“请从A-E选择”等提示
    option_lines: List[str] = []
    for i, opt in enumerate(endings):
        # endings 里通常是字符串；若出现非字符串，也做一下兼容
        opt_str = opt if isinstance(opt, str) else json.dumps(opt, ensure_ascii=False)
        option_lines.append(f"{i}. {opt_str}")

    question = (
        "Given the context, choose the correct ending.\n\n"
        f"Context:\n{context}\n\n"
        "Options:\n" + "\n".join(option_lines)
    )

    # 参考答案：正确 ending 文本
    answer_raw = endings[label]
    answer = answer_raw if isinstance(answer_raw, str) else json.dumps(answer_raw, ensure_ascii=False)

    return {
        "id": str(idx),
        "question": question,
        "answer": answer,
    }


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
    parser = argparse.ArgumentParser(description="Convert dataset JSONL into {id, question, answer} JSONL.")
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    args = parser.parse_args()

    convert_jsonl(args.input, args.output)


if __name__ == "__main__":
    main()
