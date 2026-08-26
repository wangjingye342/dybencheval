import json
import argparse
from pathlib import Path


def build_question(item):
    """
    question：包含所有提供给模型的有用信息（不包含答案）
    """
    problem_text = item.get("problem_text", "").strip()
    unit = item.get("unit", "").strip()
    source = item.get("source", "").strip()
    comment = item.get("comment", "").strip()

    question = (
        "You are given a problem. Please solve it and provide the final answer.\n\n"
        "=== Problem ===\n"
        f"{problem_text}\n\n"
    )

    if unit:
        question += f"Expected Unit: {unit}\n"
    if source:
        question += f"Source: {source}\n"
    if comment:
        question += f"Comment: {comment}\n"

    question += "\nTask: Give the final answer (and unit if applicable)."
    return question


def build_answer(item):
    """
    answer：推荐结构化输出，包含最终答案和解答过程（方便训练）
    你可以很容易改为只输出 answer_number 或 solution
    """
    answer = {
        "answer_number": item.get("answer_number", "").strip(),
        "unit": item.get("unit", "").strip(),
        "answer_latex": item.get("answer_latex", "").strip(),
        "solution": item.get("solution", "").strip()
    }
    return json.dumps(answer, ensure_ascii=False)


def build_id(item, idx):
    """
    id：优先使用 problemid，否则 fallback 行号
    """
    pid = item.get("problemid", "").strip()
    if pid:
        return pid
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
        description="Convert problem/latex/solution JSONL into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
