import json
import argparse
from pathlib import Path


def format_test_list(test_list):
    """
    将 test_list (list) 变为可读文本
    """
    if not test_list:
        return ""
    if isinstance(test_list, list):
        return "\n".join([f"- {t}" for t in test_list])
    return str(test_list)


def build_question(item):
    """
    question：包含所有对模型有用的信息
    """
    text = str(item.get("text", "")).strip()
    setup = str(item.get("test_setup_code", "")).strip()
    test_list = item.get("test_list", [])
    challenge_list = item.get("challenge_test_list", [])

    question = (
        "You are given a coding task. Write a correct solution that passes all provided tests.\n\n"
        "=== Task Description ===\n"
        f"{text}\n\n"
    )

    if setup:
        question += (
            "=== Test Setup Code ===\n"
            f"{setup}\n\n"
        )

    if test_list:
        question += (
            "=== Basic Tests ===\n"
            f"{format_test_list(test_list)}\n\n"
        )

    if challenge_list:
        question += (
            "=== Challenge Tests ===\n"
            f"{format_test_list(challenge_list)}\n\n"
        )

    question += "Task: Provide the full code solution."
    return question


def build_answer(item):
    """
    answer：参考答案 code
    """
    return str(item.get("code", "")).strip()


def build_id(item, idx):
    """
    id：优先 task_id，否则 fallback 行号
    """
    tid = item.get("task_id", None)
    if tid is not None:
        return str(tid)
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
        description="Convert code task dataset with tests JSONL into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
