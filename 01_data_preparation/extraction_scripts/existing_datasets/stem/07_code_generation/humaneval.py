import json
import argparse
from pathlib import Path


def build_question(item):
    """
    question：包含所有提供给模型的有用信息
    """
    prompt = str(item.get("prompt", "")).strip()
    entry = str(item.get("entry_point", "")).strip()
    test = str(item.get("test", "")).strip()

    question = (
        "You are given a coding task. Implement the required function.\n\n"
        "=== Task Prompt ===\n"
        f"{prompt}\n\n"
        "=== Entry Point ===\n"
        f"{entry}\n\n"
        "=== Tests ===\n"
        f"{test}\n\n"
        "Task: Write the correct code solution that passes all tests."
    )
    return question


def build_answer(item):
    """
    answer：参考答案 canonical_solution
    """
    return str(item.get("canonical_solution", "")).strip()


def build_id(item, idx):
    """
    id：优先 task_id，否则 fallback 行号
    """
    task_id = item.get("task_id", "").strip()
    if task_id:
        return task_id
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
        description="Convert code task JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
