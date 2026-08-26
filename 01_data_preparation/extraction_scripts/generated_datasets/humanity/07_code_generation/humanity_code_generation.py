import json
import argparse
from pathlib import Path


def format_test_cases(test_cases):
    """
    将 test_cases list 转成可读字符串
    """
    if not test_cases:
        return ""
    if isinstance(test_cases, list):
        # 每个测试用例可能是 dict / list / str
        return "\n".join([f"- {json.dumps(tc, ensure_ascii=False)}" for tc in test_cases])
    return str(test_cases)


def build_question(item):
    """
    question：包含所有提供给模型的有用信息
    """
    scenario = str(item.get("target_scenario", "")).strip()
    task = str(item.get("target_task", "")).strip()
    q_text = str(item.get("question", "")).strip()
    test_cases = item.get("test_cases", [])

    question = (
        "You are given a coding problem. Write a correct solution that passes all test cases.\n\n"
        f"Scenario: {scenario}\n"
        f"Task: {task}\n\n"
        "=== Problem Description ===\n"
        f"{q_text}\n\n"
        "=== Test Cases ===\n"
        f"{format_test_cases(test_cases)}\n\n"
        "Task: Provide the full solution code."
    )
    return question


def build_answer(item):
    """
    answer：参考答案 solution
    """
    return str(item.get("solution", "")).strip()


def build_id(item, idx):
    """
    id：优先使用题目 id，否则 fallback my_generated_id 或行号
    """
    pid = str(item.get("id", "")).strip()
    if pid:
        return pid

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
        description="Convert coding problems with tests JSONL into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
