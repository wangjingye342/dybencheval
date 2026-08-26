import json
import argparse
from pathlib import Path


def build_question(item):
    """
    question：包含所有提供给模型的有用信息
    """
    article = str(item.get("article", "")).strip()

    question = (
        "You are given an article. Please write the highlights / summary.\n\n"
        "=== Article ===\n"
        f"{article}\n\n"
        "Task: Generate the highlights."
    )
    return question


def build_answer(item):
    """
    answer：参考答案 highlights
    """
    return str(item.get("highlights", "")).strip()


def build_id(item, idx):
    """
    id：优先使用原始 id，否则 fallback
    """
    sid = str(item.get("id", "")).strip()
    if sid:
        return sid
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
        description="Convert article-highlights JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
