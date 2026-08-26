import json
import argparse
from pathlib import Path


def build_question(item):
    """
    question 包含所有给模型的有用信息
    """
    q = item.get("Question", "").strip()
    q_type = item.get("Type", "").strip()
    category = item.get("Category", "").strip()
    source = item.get("Source", "").strip()

    incorrect = item.get("Incorrect Answers", [])
    if isinstance(incorrect, list):
        incorrect_str = "\n".join([f"- {x}" for x in incorrect])
    else:
        incorrect_str = str(incorrect)

    question = (
        f"Type: {q_type}\n"
        f"Category: {category}\n"
        f"Source: {source}\n\n"
        f"Question:\n{q}\n\n"
        f"Incorrect Answers (for reference):\n{incorrect_str}\n\n"
        "Please provide the best correct answer."
    )
    return question


def build_answer(item):
    """
    answer 作为参考答案：
    - 优先 Best Answer
    - 如果 Best Answer 为空，则退化到 Correct Answers
    """
    best = item.get("Best Answer", None)
    if best and str(best).strip():
        return str(best).strip()

    correct = item.get("Correct Answers", None)
    if isinstance(correct, list):
        return "; ".join([str(x).strip() for x in correct if str(x).strip()])
    elif correct:
        return str(correct).strip()

    return ""


def build_id(item, idx):
    """
    自动生成 id：
    - 如果有 Source 且不为空，优先用 Source
    - 否则使用 Type_Category_idx
    """
    source = item.get("Source", None)
    if source and str(source).strip():
        return str(source).strip()

    q_type = str(item.get("Type", "Unknown")).strip()
    category = str(item.get("Category", "Unknown")).strip()
    return f"{q_type}_{category}_{idx}"


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
    parser = argparse.ArgumentParser(description="Convert QA JSONL dataset into training format (id/question/answer)")
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
