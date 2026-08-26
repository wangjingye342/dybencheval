import json
import argparse
from pathlib import Path


def build_question(item):
    """
    question：包含所有提供给模型的有用信息
    """
    name = str(item.get("name", "")).strip()
    metadata = item.get("metadata", {})

    question = (
        "You are given an item name and its metadata. "
        "Use the metadata to produce the correct structured output.\n\n"
        f"Name: {name}\n\n"
        "=== Metadata (JSON) ===\n"
        f"{json.dumps(metadata, ensure_ascii=False, indent=2)}\n\n"
        "Task: Output the structured metadata."
    )
    return question


def build_answer(item):
    """
    answer：默认完整输出 metadata，保留所有信息
    """
    metadata = item.get("metadata", {})
    return json.dumps(metadata, ensure_ascii=False)


def build_id(item, idx):
    """
    id：name + idx
    """
    name = str(item.get("name", "sample")).strip().replace(" ", "_")
    return f"{name}_{idx}"


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
        description="Convert name+metadata JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
