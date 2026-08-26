import json
import argparse
from pathlib import Path


def build_question(item):
    """
    question：包含所有提供给模型的有用信息
    """
    q = str(item.get("Question", "")).strip()
    answer_type = str(item.get("Answer_type", "")).strip()
    picture = item.get("Picture", None)

    question = (
        "You are given a question. Please answer it according to the expected answer type.\n\n"
        f"Answer Type: {answer_type}\n\n"
        f"Question:\n{q}\n\n"
    )

    if picture is not None and str(picture).strip():
        question += f"Picture Reference: {picture}\n\n"

    question += "Task: Provide the correct answer."
    return question


def build_answer(item):
    """
    answer：参考答案
    """
    return str(item.get("Answer", "")).strip()


def build_id(idx):
    """
    id：行号
    """
    return f"sample_{idx}"


def convert_dataset(input_file, output_file):
    input_path = Path(input_file)
    output_path = Path(output_file)

    results = []
    with input_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            item = json.loads(line)

            sample_id = build_id(idx)
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
        description="Convert QA(+picture) JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
