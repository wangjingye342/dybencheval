import json
import argparse
from pathlib import Path


def format_metadata(metadata: dict):
    """
    将 metadata dict 转换成可读文本
    """
    if not metadata:
        return ""
    parts = []
    for k, v in metadata.items():
        parts.append(f"{k}: {v}")
    return "\n".join(parts)


def build_question(item):
    """
    question：包含所有给模型的有用信息
    """
    prompt = str(item.get("prompt", "")).strip()
    code_context = str(item.get("code_context", "")).strip()
    metadata = item.get("metadata", {})

    question = (
        "You are given a coding task. Use the metadata and code context if provided.\n\n"
        "=== Metadata ===\n"
        f"{format_metadata(metadata)}\n\n"
        "=== Task Prompt ===\n"
        f"{prompt}\n\n"
        "=== Code Context ===\n"
        f"{code_context}\n\n"
        "Task: Write the correct code solution."
    )
    return question


def build_answer(item):
    """
    answer：参考答案 reference_code
    """
    return str(item.get("reference_code", "")).strip()


def build_id(item, idx):
    """
    id：优先从 metadata 里找可用唯一字段，否则 fallback
    """
    metadata = item.get("metadata", {})
    for key in ["id", "task_id", "uid", "uuid", "name"]:
        if key in metadata and str(metadata[key]).strip():
            return str(metadata[key]).strip()
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
        description="Convert code generation JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
