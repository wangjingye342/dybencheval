import json
import argparse
from pathlib import Path


def build_question(item):
    """
    question：包含所有提供给模型的有用信息
    """
    scenario = str(item.get("target_scenario", "")).strip()
    task = str(item.get("target_task", "")).strip()
    topic = str(item.get("topic", "")).strip()
    context_type = str(item.get("context_type", "")).strip()
    input_prompt = str(item.get("input_prompt", "")).strip()

    question = (
        "You are given a task prompt and metadata. Produce the expected output.\n\n"
        f"Scenario: {scenario}\n"
        f"Task: {task}\n"
        f"Topic: {topic}\n"
        f"Context Type: {context_type}\n\n"
        "=== Input Prompt ===\n"
        f"{input_prompt}\n\n"
        "Task: Produce the correct output."
    )
    return question


def build_answer(item):
    """
    answer：参考答案 expected_output
    """
    return str(item.get("expected_output", "")).strip()


def build_id(item, idx):
    """
    id：优先使用 my_generated_id，否则 fallback 行号
    """
    gid = item.get("my_generated_id", None)
    if gid is not None:
        return str(gid)
    return f"sample_{idx}"


def convert_dataset(input_file, output_file):
    input_path = Path(input_file)
    output_path = Path(output_file)

    results = []
    with input_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            item = json.loads(line)

            results.append({
                "id": build_id(item, idx),
                "question": build_question(item),
                "answer": build_answer(item)
            })

    with output_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Converted {len(results)} samples -> {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert prompt-expected_output JSONL into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
