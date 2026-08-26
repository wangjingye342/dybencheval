#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
from typing import Any, Dict, List, Optional, Tuple


def _as_str(x: Any) -> str:
    if isinstance(x, str):
        return x
    return json.dumps(x, ensure_ascii=False)


# =========================
# Schema 1: conversation_id + utterances[]
# =========================

def _format_utterance(u: Dict[str, Any], include_entities: bool) -> str:
    speaker = _as_str(u.get("speaker", "UNKNOWN"))
    text = _as_str(u.get("text", "")).strip()

    if not include_entities:
        return f"{speaker}: {text}"

    # segments: [{'text': 'Us', 'annotations':[{'name':'movie_ticket.name.movie'}], ...}, ...]
    ents: List[str] = []
    segs = u.get("segments")
    if isinstance(segs, list):
        for s in segs:
            if not isinstance(s, dict):
                continue
            seg_text = s.get("text")
            anns = s.get("annotations")
            if not isinstance(seg_text, str) or not isinstance(anns, list):
                continue
            for a in anns:
                if isinstance(a, dict) and isinstance(a.get("name"), str):
                    ents.append(f"{seg_text}::{a['name']}")

    if ents:
        # 去重但保序
        seen = set()
        ents_uniq = []
        for e in ents:
            if e not in seen:
                seen.add(e)
                ents_uniq.append(e)
        return f"{speaker}: {text}\n  [entities] " + ", ".join(ents_uniq)

    return f"{speaker}: {text}"


def _convert_conversation(obj: Dict[str, Any], line_idx: int, include_entities: bool) -> Optional[List[Dict[str, str]]]:
    conv_id = obj.get("conversation_id")
    utterances = obj.get("utterances")

    if not isinstance(utterances, list):
        return None

    base_id = str(conv_id) if conv_id is not None else str(line_idx)

    out: List[Dict[str, str]] = []
    history: List[Dict[str, Any]] = []

    for u in utterances:
        if not isinstance(u, dict):
            continue
        speaker = u.get("speaker")
        text = u.get("text")
        idx = u.get("index")

        if not isinstance(speaker, str) or not isinstance(text, str):
            continue

        speaker_u = speaker.upper()
        if speaker_u == "ASSISTANT":
            hist_lines = [_format_utterance(h, include_entities) for h in history]
            hist_text = "\n".join(hist_lines).strip() if hist_lines else "(empty)"

            question = (
                "You are a helpful assistant in a task-oriented conversation.\n"
                "Given the conversation so far, write the next ASSISTANT response.\n\n"
                "Conversation:\n"
                f"{hist_text}"
            )

            turn_id = str(idx) if idx is not None else str(len(out))
            out.append(
                {
                    "id": f"{base_id}_{turn_id}",
                    "question": question,
                    "answer": text.strip(),
                }
            )

            # 把当前 assistant turn 放入历史，供后续 turn 使用
            history.append(u)
        else:
            history.append(u)

    return out if out else None


# =========================
# Schema 2: intent/rewritten_intent/snippet/question_id
# =========================

def _convert_intent_snippet(obj: Dict[str, Any], line_idx: int) -> Optional[Dict[str, str]]:
    intent = obj.get("intent")
    rewritten = obj.get("rewritten_intent")
    snippet = obj.get("snippet")
    qid = obj.get("question_id")

    if not isinstance(intent, str) or not isinstance(snippet, str):
        return None

    out_id = str(qid) if qid is not None else str(line_idx)

    # question 尽量放“可用信息”：rewritten_intent 更清晰就优先
    main_intent = rewritten.strip() if isinstance(rewritten, str) and rewritten.strip() else intent.strip()

    question = (
        "Write a concise and correct code snippet that satisfies the intent.\n\n"
        f"Intent:\n{main_intent}"
    )

    # 也把原 intent 留作参考（如果 rewritten 存在）
    if isinstance(rewritten, str) and rewritten.strip() and rewritten.strip() != intent.strip():
        question += f"\n\nOriginal intent:\n{intent.strip()}"

    return {"id": out_id, "question": question, "answer": snippet.strip()}


# =========================
# Main convert
# =========================

def convert_jsonl(input_path: str, output_path: str, include_entities: bool) -> None:
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
                obj = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue

            if not isinstance(obj, dict):
                skipped += 1
                continue

            # 自动识别 schema
            qa_many: Optional[List[Dict[str, str]]] = None
            qa_one: Optional[Dict[str, str]] = None

            # Schema 1
            if "conversation_id" in obj and "utterances" in obj:
                qa_many = _convert_conversation(obj, i, include_entities=include_entities)

            # Schema 2
            elif "intent" in obj and "snippet" in obj:
                qa_one = _convert_intent_snippet(obj, i)

            else:
                skipped += 1
                continue

            if qa_many is not None:
                for qa in qa_many:
                    fout.write(json.dumps(qa, ensure_ascii=False) + "\n")
                    written += 1
                continue

            if qa_one is not None:
                fout.write(json.dumps(qa_one, ensure_ascii=False) + "\n")
                written += 1
                continue

            skipped += 1

    print(f"Done. Written={written}, Skipped={skipped}, TotalLines={total}")
    print(f"Output saved to: {output_path}")
    if written == 0:
        print("WARNING: Written=0. Likely schema mismatch or all lines failed parsing.")


def main():
    parser = argparse.ArgumentParser(
        description="Convert JSONL datasets into training JSONL with {id, question, answer}."
    )
    parser.add_argument("--input", required=True, help="Path to input .jsonl file")
    parser.add_argument("--output", required=True, help="Path to output .jsonl file")
    parser.add_argument(
        "--include_entities",
        action="store_true",
        help="For conversation dataset: include entity annotations (from segments) inside the question.",
    )
    args = parser.parse_args()

    convert_jsonl(args.input, args.output, include_entities=args.include_entities)


if __name__ == "__main__":
    main()
