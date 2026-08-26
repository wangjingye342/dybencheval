#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple


def _as_str(x: Any) -> str:
    if isinstance(x, str):
        return x
    return json.dumps(x, ensure_ascii=False)


def _join_text_list(x: Any) -> str:
    if isinstance(x, list):
        return "\n".join(_as_str(t) for t in x if _as_str(t).strip()).strip()
    if isinstance(x, str):
        return x.strip()
    return ""


def _table_to_markdown(table: Any, max_rows: int = 80, max_cols: int = 30) -> str:
    """把二维表转成 Markdown 表格，便于模型读取。"""
    if not isinstance(table, list) or not table:
        return ""

    rows: List[List[str]] = []
    for r in table[:max_rows]:
        if isinstance(r, list):
            rows.append([_as_str(c).replace("\n", " ").strip() for c in r[:max_cols]])
        else:
            rows.append([_as_str(r).replace("\n", " ").strip()])

    if not rows:
        return ""

    ncol = max(len(r) for r in rows)
    for r in rows:
        if len(r) < ncol:
            r.extend([""] * (ncol - len(r)))

    def esc(cell: str) -> str:
        return cell.replace("|", "\\|")

    header = rows[0]
    body = rows[1:] if len(rows) > 1 else []

    md = []
    md.append("| " + " | ".join(esc(c) for c in header) + " |")
    md.append("| " + " | ".join(["---"] * ncol) + " |")
    for r in body:
        md.append("| " + " | ".join(esc(c) for c in r) + " |")
    return "\n".join(md)


def _pick_id(ex: Dict[str, Any], line_idx: int) -> str:
    for k in ["id", "uid", "qid", "question_id", "example_id", "key", "filename"]:
        v = ex.get(k)
        if v is not None and _as_str(v).strip():
            # filename 可能很长，作为兜底 id 可以，但建议仍加行号避免重复
            if k == "filename":
                return f"{_as_str(v)}#{line_idx}"
            return _as_str(v)
    return str(line_idx)


def _extract_target(qa: Dict[str, Any], target: str) -> Optional[str]:
    if target == "answer":
        for k in ["answer", "exe_ans", "execution_answer", "final_answer", "gold_answer"]:
            v = qa.get(k)
            if v is None:
                continue
            s = _as_str(v).strip()
            if s:
                return s
        return None

    if target == "program":
        v = qa.get("program")
        s = _as_str(v).strip() if v is not None else ""
        return s if s else None

    if target == "explanation":
        v = qa.get("explanation")
        s = _as_str(v).strip() if v is not None else ""
        return s if s else None

    return None


def _build_model_input_map(model_input: Any) -> Dict[str, str]:
    """
    qa.model_input 常见形式：[[ind, text], [ind, text], ...]
    """
    mp: Dict[str, str] = {}
    if isinstance(model_input, list):
        for item in model_input:
            if isinstance(item, list) and len(item) >= 2:
                ind, txt = item[0], item[1]
                if isinstance(ind, str) and isinstance(txt, str) and ind.strip() and txt.strip():
                    mp[ind.strip()] = txt.strip()
    return mp


def _resolve_ind_to_text(
    ind: str,
    model_input_map: Dict[str, str],
    table_ori: Any,
    text_rows: List[str],
) -> Optional[str]:
    ind = ind.strip()
    if not ind:
        return None

    if ind in model_input_map:
        return model_input_map[ind]

    m = re.fullmatch(r"table_(\d+)", ind)
    if m and isinstance(table_ori, list):
        i = int(m.group(1))
        if 0 <= i < len(table_ori):
            row = table_ori[i]
            if isinstance(row, list):
                return " | ".join(_as_str(c).replace("\n", " ").strip() for c in row)
            return _as_str(row).replace("\n", " ").strip()

    m = re.fullmatch(r"text_(\d+)", ind)
    if m:
        i = int(m.group(1))
        if 0 <= i < len(text_rows):
            return text_rows[i].replace("\n", " ").strip()

    return None


def _collect_retrieved_inds(retrieved: Any, topk: int) -> List[str]:
    """
    retrieved 常见：[{score:..., ind:"table_4"}, ...]
    """
    if not isinstance(retrieved, list) or not retrieved:
        return []
    inds: List[str] = []
    for d in retrieved[:topk]:
        if isinstance(d, dict) and isinstance(d.get("ind"), str):
            inds.append(d["ind"])
    return inds


def build_qa(
    example: Dict[str, Any],
    line_idx: int,
    target: str,
    context_mode: str,
    include_retrieved_all: bool,
    topk: int,
    max_rows: int,
    max_cols: int,
) -> Optional[Dict[str, str]]:
    qa = example.get("qa")
    if not isinstance(qa, dict):
        return None

    q = qa.get("question")
    if not isinstance(q, str) or not q.strip():
        return None

    answer = _extract_target(qa, target=target)
    if answer is None:
        return None

    out_id = _pick_id(example, line_idx)

    filename = example.get("filename")
    pre_text = example.get("pre_text")
    post_text = example.get("post_text")
    table_ori = example.get("table_ori") if example.get("table_ori") is not None else example.get("table")

    # 用于 text_0/text_1 的简单映射（如果数据里就是这么编号）
    text_rows = []
    pre = _join_text_list(pre_text)
    post = _join_text_list(post_text)
    # 这里把 pre_text/post_text 的“逐行”保留，便于 text_i 索引
    if isinstance(pre_text, list):
        text_rows.extend([_as_str(x) for x in pre_text])
    if isinstance(post_text, list):
        text_rows.extend([_as_str(x) for x in post_text])

    file_block = f"Document: {_as_str(filename)}\n\n" if filename is not None else ""

    if context_mode == "retrieved":
        model_input_map = _build_model_input_map(qa.get("model_input"))

        inds: List[str] = []
        # 先用 model_input 里的 ind 顺序作为基础证据（通常就是给模型看的）
        inds.extend(list(model_input_map.keys()))

        # 再追加检索字段指到的 ind
        if include_retrieved_all:
            inds.extend(_collect_retrieved_inds(example.get("table_retrieved_all"), topk=topk))
            inds.extend(_collect_retrieved_inds(example.get("text_retrieved_all"), topk=topk))
        else:
            inds.extend(_collect_retrieved_inds(example.get("table_retrieved"), topk=topk))
            inds.extend(_collect_retrieved_inds(example.get("text_retrieved"), topk=topk))

        # 去重保序
        seen = set()
        uniq_inds = []
        for x in inds:
            if x not in seen:
                seen.add(x)
                uniq_inds.append(x)

        evid_lines: List[str] = []
        for ind in uniq_inds:
            txt = _resolve_ind_to_text(ind, model_input_map, table_ori, text_rows)
            if txt:
                evid_lines.append(f"- {ind}: {txt}")

        evidence_block = "Evidence:\n" + ("\n".join(evid_lines) if evid_lines else "- (none)") + "\n\n"

        prompt = (
            "Answer the financial question using the provided evidence.\n\n"
            + file_block
            + evidence_block
            + f"Question:\n{q.strip()}\n\n"
            + "Return only the final answer."
        )

    else:
        table_md = _table_to_markdown(table_ori, max_rows=max_rows, max_cols=max_cols)
        pre_block = f"Text before table:\n{pre}\n\n" if pre else ""
        table_block = f"Table:\n{table_md}\n\n" if table_md else ""
        post_block = f"Text after table:\n{post}\n\n" if post else ""

        prompt = (
            "Answer the financial question using the given table and surrounding text.\n\n"
            + file_block
            + pre_block
            + table_block
            + post_block
            + f"Question:\n{q.strip()}\n\n"
            + "Return only the final answer."
        )

    return {"id": out_id, "question": prompt, "answer": answer}


def convert_jsonl(
    input_path: str,
    output_path: str,
    target: str,
    context_mode: str,
    include_retrieved_all: bool,
    topk: int,
    max_rows: int,
    max_cols: int,
) -> None:
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

            qa = build_qa(
                ex,
                i,
                target=target,
                context_mode=context_mode,
                include_retrieved_all=include_retrieved_all,
                topk=topk,
                max_rows=max_rows,
                max_cols=max_cols,
            )
            if qa is None:
                skipped += 1
                continue

            fout.write(json.dumps(qa, ensure_ascii=False) + "\n")
            written += 1

    print(f"Done. Written={written}, Skipped={skipped}, TotalLines={total}")
    print(f"Output saved to: {output_path}")
    if written == 0:
        print("WARNING: Written=0. Check schema/target fields.")


def main():
    parser = argparse.ArgumentParser(
        description="Convert FinQA-like JSONL into training JSONL with {id, question, answer}."
    )
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    parser.add_argument(
        "--target",
        choices=["answer", "program", "explanation"],
        default="answer",
        help="Supervision target from qa: answer/program/explanation",
    )
    parser.add_argument(
        "--context_mode",
        choices=["full", "retrieved"],
        default="full",
        help="full: use pre_text+table+post_text; retrieved: use qa.model_input + retrieved inds",
    )
    parser.add_argument(
        "--include_retrieved_all",
        action="store_true",
        help="Use *_retrieved_all fields instead of *_retrieved (default: False).",
    )
    parser.add_argument("--topk", type=int, default=8, help="Top-k retrieved inds to include (for retrieved mode).")
    parser.add_argument("--max_rows", type=int, default=80, help="Max table rows in full mode.")
    parser.add_argument("--max_cols", type=int, default=30, help="Max table cols in full mode.")
    args = parser.parse_args()

    convert_jsonl(
        args.input,
        args.output,
        target=args.target,
        context_mode=args.context_mode,
        include_retrieved_all=args.include_retrieved_all,
        topk=args.topk,
        max_rows=args.max_rows,
        max_cols=args.max_cols,
    )


if __name__ == "__main__":
    main()
