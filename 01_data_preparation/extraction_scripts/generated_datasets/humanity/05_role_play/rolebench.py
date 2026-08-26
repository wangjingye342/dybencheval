import json
import argparse
from pathlib import Path


def build_question(item):
    """
    question：包含所有对模型有用的信息
    """
    role = str(item.get("role", "")).strip()
    qtype = str(item.get("type", "")).strip()
    q = str(item.get("question", "")).strip()

    question = (
        "You are given a question and some task metadata. Provide the best answer.\n\n"
        f"Role: {role}\n"
        f"Type: {qtype}\n\n"
        f"Question:\n{q}\n\n"
        "Task: Provide the best response."
    )
    return question


def build_answer(item):
    """
    answer：保留 generated list 的所有候选，作为 JSON 字符串输出
    """
    generated = item.get("generated", [])
    return json.dumps(generated, ensure_ascii=False)


def build_id(item, idx):
    """
    id：默认 role_type_idx
    """
    role = str(item.get("role", "role")).strip()
    qtype = str(item.get("type", "type")).strip()
    return f"{role}_{qtype}_{idx}"


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
        description="Convert multi-generated JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
