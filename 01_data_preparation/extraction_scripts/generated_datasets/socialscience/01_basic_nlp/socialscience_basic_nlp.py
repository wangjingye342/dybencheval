import json
import argparse
from pathlib import Path


def format_tokens_and_tags(tokens, tags):
    """
    将 tokens 与 ner_tags 对齐展示
    """
    if not tokens:
        return ""
    if not tags or len(tags) != len(tokens):
        return " ".join(tokens)

    lines = []
    for t, tag in zip(tokens, tags):
        lines.append(f"{t}\t{tag}")
    return "\n".join(lines)


def build_question(item, include_ner_tags=True):
    """
    question：包含所有提供给模型的有用信息
    include_ner_tags=True 时会把 ner_tags 提供给模型
    """
    scenario = str(item.get("scenario", "")).strip()
    target_scenario = str(item.get("target_scenario", "")).strip()
    target_task = str(item.get("target_task", "")).strip()

    text = str(item.get("text", "")).strip()
    tokens = item.get("tokens", [])
    ner_tags = item.get("ner_tags", [])

    question = (
        "You are given an NLU task. Extract the intent and entities from the text.\n\n"
        f"Scenario: {scenario}\n"
        f"Target Scenario: {target_scenario}\n"
        f"Target Task: {target_task}\n\n"
        "=== Text ===\n"
        f"{text}\n\n"
    )

    if tokens:
        question += "=== Tokens ===\n"
        question += " ".join(tokens) + "\n\n"

    if include_ner_tags and tokens and ner_tags:
        question += "=== Token-level NER Tags (Optional) ===\n"
        question += format_tokens_and_tags(tokens, ner_tags) + "\n\n"

    question += "Task: Output the intent classification and extracted entities."
    return question


def build_answer(item):
    """
    answer：结构化输出 intent + entity_extraction + ner_tags
    """
    answer = {
        "intent_classification": item.get("intent_classification", ""),
        "entity_extraction": item.get("entity_extraction", {}),
        "ner_tags": item.get("ner_tags", [])
    }
    return json.dumps(answer, ensure_ascii=False)


def build_id(item, idx):
    """
    id：优先使用 id，否则 fallback my_generated_id 或行号
    """
    sid = str(item.get("id", "")).strip()
    if sid:
        return sid

    gid = item.get("my_generated_id", None)
    if gid is not None:
        return str(gid)

    return f"sample_{idx}"


def convert_dataset(input_file, output_file, include_ner_tags=True):
    input_path = Path(input_file)
    output_path = Path(output_file)

    results = []
    with input_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            item = json.loads(line)

            results.append({
                "id": build_id(item, idx),
                "question": build_question(item, include_ner_tags=include_ner_tags),
                "answer": build_answer(item)
            })

    with output_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Converted {len(results)} samples -> {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert NLU intent+NER JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")
    parser.add_argument(
        "--exclude_ner_tags",
        action="store_true",
        help="If set, do NOT include ner_tags in question (default includes)"
    )

    args = parser.parse_args()
    include_ner_tags = not args.exclude_ner_tags
    convert_dataset(args.input, args.output, include_ner_tags=include_ner_tags)


if __name__ == "__main__":
    main()
