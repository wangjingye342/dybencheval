#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import re
from typing import Any, Dict, List, Optional


def _as_str(x: Any) -> str:
    """把任意对象稳定转成字符串（保留中文/非ASCII）"""
    if isinstance(x, str):
        return x
    return json.dumps(x, ensure_ascii=False)


def _join_dialogue(dialogue: Any) -> Optional[str]:
    if not isinstance(dialogue, list):
        return None
    return "\n".join(_as_str(turn) for turn in dialogue)


def _parse_mr(mr: str) -> List[str]:
    """
    解析 E2E/NLG 风格的 mr：
      name[The Mill], eatType[pub], priceRange[less than £20]
    输出为可读的 key: value 列表字符串行。
    """
    parts = [p.strip() for p in mr.split(",") if p.strip()]
    kv_lines: List[str] = []
    for p in parts:
        # 允许 value 中出现逗号被 split 打断的极端情况很少见；这里按常见格式处理
        m = re.match(r"^([^\[]+)\[(.*)\]$", p)
        if m:
            k = m.group(1).strip()
            v = m.group(2).strip()
            kv_lines.append(f"- {k}: {v}")
        else:
            kv_lines.append(f"- {p}")
    return kv_lines


# ------------------------- Schema A: context/endings/label -------------------------
def _convert_context_endings_label(example: Dict[str, Any], idx: int) -> Optional[Dict[str, str]]:
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


# ------------------------- Schema B: question/choices/answer(+subject) -------------------------
def _convert_question_choices_answer(example: Dict[str, Any], idx: int) -> Optional[Dict[str, str]]:
    q = example.get("question")
    choices = example.get("choices")
    ans = example.get("answer")
    subject = example.get("subject")

    if not isinstance(q, str) or not isinstance(choices, list):
        return None

    # answer 兼容：索引 or 文本
    if isinstance(ans, int):
        if not (0 <= ans < len(choices)):
            return None
        answer_text = _as_str(choices[ans])
    elif isinstance(ans, str):
        answer_text = ans
    else:
        return None

    option_lines = [f"{i}. {_as_str(opt)}" for i, opt in enumerate(choices)]
    subject_block = f"Subject: {_as_str(subject)}\n\n" if subject is not None else ""

    question = (
        subject_block
        + "Answer the following multiple-choice question.\n\n"
        f"Question:\n{q}\n\n"
        "Options:\n" + "\n".join(option_lines)
    )

    return {"id": str(idx), "question": question, "answer": answer_text}


# ------------------------- Schema C: dialogue/relations (relation extraction) -------------------------
def _convert_dialogue_relations(example: Dict[str, Any], idx: int) -> Optional[List[Dict[str, str]]]:
    dialogue = example.get("dialogue")
    relations = example.get("relations")

    if dialogue is None or relations is None:
        return None
    if not isinstance(relations, list):
        return None

    dialogue_text = _join_dialogue(dialogue)
    if dialogue_text is None:
        return None

    out: List[Dict[str, str]] = []
    for j, rel in enumerate(relations):
        if not isinstance(rel, dict):
            continue

        x = rel.get("x")
        y = rel.get("y")
        r = rel.get("r")      # 通常是 list[str] 或 str
        t = rel.get("t")      # 可选 evidence/trigger
        x_type = rel.get("x_type")
        y_type = rel.get("y_type")

        if not isinstance(x, str) or not isinstance(y, str):
            continue

        # 关系标签
        if isinstance(r, list):
            answer = "; ".join(_as_str(item) for item in r if _as_str(item).strip())
            answer = answer.strip() if answer.strip() else "unanswerable"
        elif isinstance(r, str):
            answer = r.strip() if r.strip() else "unanswerable"
        else:
            continue

        trigger = ""
        if isinstance(t, list):
            tt = [(_as_str(z)).strip() for z in t if (_as_str(z)).strip()]
            if tt:
                trigger = "Trigger/Evidence: " + " | ".join(tt) + "\n\n"
        elif isinstance(t, str) and t.strip():
            trigger = f"Trigger/Evidence: {t.strip()}\n\n"

        type_info = ""
        if x_type is not None or y_type is not None:
            type_info = f"Entity types: x_type={_as_str(x_type)}, y_type={_as_str(y_type)}\n\n"

        question = (
            "Extract the relation between two entities from the dialogue.\n\n"
            f"Dialogue:\n{dialogue_text}\n\n"
            f"Entity pair:\n- x: {x}\n- y: {y}\n\n"
            f"{type_info}"
            f"{trigger}"
            "Return the relation label(s) for the pair."
        )

        out.append({"id": f"{idx}_{j}", "question": question, "answer": answer})

    return out if out else None


# ------------------------- Schema D: mr/ref (data-to-text) -------------------------
def _convert_mr_ref(example: Dict[str, Any], idx: int) -> Optional[Dict[str, str]]:
    mr = example.get("mr")
    ref = example.get("ref")

    if not isinstance(mr, str) or not isinstance(ref, str):
        return None

    kv_lines = _parse_mr(mr)
    question = (
        "Generate a fluent natural language description based on the meaning representation (MR).\n\n"
        f"MR (raw):\n{mr}\n\n"
        "MR (parsed):\n" + "\n".join(kv_lines)
    )
    answer = ref

    return {"id": str(idx), "question": question, "answer": answer}


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

            qa_single: Optional[Dict[str, str]] = None

            # Schema A
            if ("context" in example and "endings" in example and "label" in example):
                qa_single = _convert_context_endings_label(example, idx)

            # Schema B
            elif ("question" in example and "choices" in example and "answer" in example):
                qa_single = _convert_question_choices_answer(example, idx)

            # Schema C (one-to-many)
            elif ("dialogue" in example and "relations" in example):
                qa_many = _convert_dialogue_relations(example, idx)
                if qa_many is None:
                    skipped += 1
                    continue
                for qa in qa_many:
                    fout.write(json.dumps(qa, ensure_ascii=False) + "\n")
                    written += 1
                continue

            # Schema D
            elif ("mr" in example and "ref" in example):
                qa_single = _convert_mr_ref(example, idx)

            if qa_single is None:
                skipped += 1
                continue

            fout.write(json.dumps(qa_single, ensure_ascii=False) + "\n")
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
