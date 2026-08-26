import json
import argparse
from pathlib import Path


def build_question(item):
    """
    question：包含所有给模型的有用信息
    """
    file_ref = str(item.get("file", "")).strip()
    message = str(item.get("message", "")).strip()

    question = (
        "You are given a file reference and a message extracted from that file. "
        "Please reproduce or summarize the message based on the context.\n\n"
        f"File: {file_ref}\n\n"
        "=== Message ===\n"
        f"{message}\n\n"
        "Task: Output the message."
    )
    return question


def build_answer(item):
    """
    answer：参考答案 message
    """
    return str(item.get("message", "")).strip()


def build_id(item, idx):
    """
    id：file + 行号，保证稳定
    """
    file_ref = str(item.get("file", "file")).strip().replace("/", "_").replace("\\", "_")
    return f"{file_ref}_{idx}"


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
        description="Convert file-message JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
