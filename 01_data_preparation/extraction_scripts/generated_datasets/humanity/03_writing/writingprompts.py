import json
import argparse
from pathlib import Path


def build_question(item):
    """
    question：包含所有对模型有用的信息
    """
    prompt = str(item.get("prompt", "")).strip()

    question = (
        "You are given a writing prompt. Please write a complete story based on the prompt.\n\n"
        f"Prompt:\n{prompt}\n\n"
        "Task: Generate the story."
    )
    return question


def build_answer(item):
    """
    answer：参考答案 story
    """
    return str(item.get("story", "")).strip()


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
        description="Convert prompt-story JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
