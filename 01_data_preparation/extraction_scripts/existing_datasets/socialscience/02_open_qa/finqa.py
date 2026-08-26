#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
from typing import Any, Dict, List, Optional, Union


def _as_str(x: Any) -> str:
    if isinstance(x, str):
        return x
    return json.dumps(x, ensure_ascii=False)


def _join_text_list(xs: Any) -> str:
    """pre_text/post_text 常见是 list[str]，也兼容 str/其他"""
    if isinstance(xs, list):
        return "\n".join(_as_str(t) for t in xs if _as_str(t).strip()).strip()
    if isinstance(xs, str):
        return xs.strip()
    return _as_str(xs).strip()


def _table_to_markdown(table: Any, max_rows: int = 80, max_cols: int = 30) -> str:
    """
    将 table_ori(list[list[str]]) 转成 Markdown 表格，便于模型读取。
    如果表特别大，可通过 max_rows/max_cols 截断（默认很宽松）。
    """
    if not isinstance(table, list) or not table:
        return ""

    # 取前 max_rows 行，且每行截断到 max_cols 列
    rows: List[List[str]] = []
    for r in table[:max_rows]:
        if isinstance(r, list):
            rows.append([_as_str(c).replace("\n", " ").strip() for c in r[:max_cols]])
        else:
            rows.append([_as_str(r).replace("\n", " ").strip()])

    if not rows:
        return ""

    # 统一列数（按最大列数补空）
    ncol = max(len(r) for r in rows)
    for r in rows:
        if len(r) < ncol:
            r.extend([""] * (ncol - len(r)))

    header = rows[0]
    body = rows[1:] if len(rows) > 1 else []

    # Markdown 表格
    def esc(cell: str) -> str:
        return cell.replace("|", "\\|")

    md = []
    md.append("| " + " | ".join(esc(c) for c in header) + " |")
    md.append("| " + " | ".join(["---"] * ncol) + " |")
    for r in body:
        md.append("| " + " | ".join(esc(c) for c in r) + " |")

    return "\n".join(md)


def _extract_qas(qa_field: Any) -> List[Dict[str, Any]]:
    """
    qa 可能是 dict，也可能是 list[dict]
    """
    if isinstance(qa_field, dict):
        return [qa_field]
    if isinstance(qa_field, list):
        return [q for q in qa_field if isinstance(q, dict)]
    return []


def convert_one(example: Dict[str, Any], line_idx: int) -> Optional[List[Dict[str, str]]]:
    ex_id = example.get("id")
    filename = example.get("filename")
    pre_text = example.get("pre_text")
    post_text = example.get("post_text")
    table_ori = example.get("table_ori")
    qa_field = example.get("qa")

    qas = _extract_qas(qa_field)
    if not qas:
        return None

    base_id = str(ex_id) if ex_id is not None else str(line_idx)

    pre = _join_text_list(pre_text)
    post = _join_text_list(post_text)
    table_md = _table_to_markdown(table_ori)

    # 组装 context（尽量把可用信息都提供给模型）
    file_block = f"Document: {_as_str(filename)}\n\n" if filename is not None else ""
    pre_block = f"Text before table:\n{pre}\n\n" if pre else ""
    table_block = f"Table:\n{table_md}\n\n" if table_md else ""
    post_block = f"Text after table:\n{post}\n\n" if post else ""

    out: List[Dict[str, str]] = []
    for j, qa in enumerate(qas):
        q = qa.get("question")
        a = qa.get("answer")

        if not isinstance(q, str):
            continue
        # answer 可能是数字/字符串/其他
        if a is None:
            continue
        answer = a if isinstance(a, str) else _as_str(a)

        question = (
            "Answer the question using the given table and surrounding text.\n\n"
            + file_block
            + pre_block
            + table_block
            + post_block
            + f"Question:\n{q.strip()}\n\n"
            + "Return only the final answer."
        )

        out.append({"id": f"{base_id}_{j}" if len(qas) > 1 else base_id, "question": question, "answer": answer.strip()})

    return out if out else None


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

            qas = convert_one(ex, i)
            if not qas:
                skipped += 1
                continue

            for qa in qas:
                fout.write(json.dumps(qa, ensure_ascii=False) + "\n")
                written += 1

    print(f"Done. Written={written}, Skipped={skipped}, TotalLines={total}")
    print(f"Output saved to: {output_path}")
    if written == 0:
        print("WARNING: Written=0. Likely schema mismatch or all lines failed parsing.")


def main():
    parser = argparse.ArgumentParser(
        description="Convert table-QA JSONL into training JSONL with {id, question, answer}."
    )
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    args = parser.parse_args()

    convert_jsonl(args.input, args.output)


if __name__ == "__main__":
    main()
