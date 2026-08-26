import json
import argparse
from pathlib import Path


def build_question(item):
    """
    question：包含所有提供给模型的有用信息
    """
    gid = item.get("my_generated_id", "")
    target_scenario = str(item.get("target_scenario", "")).strip()
    target_task = str(item.get("target_task", "")).strip()
    scenario = str(item.get("scenario", "")).strip()
    sub_scenario = str(item.get("sub_scenario", "")).strip()
    task = str(item.get("task", "")).strip()
    instruction = str(item.get("instruction", "")).strip()
    input_data = item.get("input_data", {})

    question = (
        "You are given an instruction and structured input data. Follow the instruction and produce the required output.\n\n"
        f"Generated ID: {gid}\n"
        f"Target Scenario: {target_scenario}\n"
        f"Target Task: {target_task}\n"
        f"Scenario: {scenario}\n"
        f"Sub-scenario: {sub_scenario}\n"
        f"Task: {task}\n\n"
        "=== Instruction ===\n"
        f"{instruction}\n\n"
        "=== Input Data (JSON) ===\n"
        f"{json.dumps(input_data, ensure_ascii=False, indent=2)}\n\n"
        "Task: Produce the correct output."
    )
    return question


def build_answer(item):
    """
    answer：参考答案 output_text
    """
    return str(item.get("output_text", "")).strip()


def build_id(item, idx):
    """
    id：优先使用 my_generated_id，否则 fallback
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

            sample_id = build_id(item, idx)
            question = build_question(item)
            answer = build_answer(item)

            results.append({
                "id": sample_id,
                "question": question,
                "answer": answer
            })

    with output_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Converted {len(results)} samples -> {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert instruction+input_data JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
