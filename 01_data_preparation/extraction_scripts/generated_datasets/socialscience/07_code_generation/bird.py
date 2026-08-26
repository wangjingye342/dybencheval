import json
import argparse
from pathlib import Path


def build_question(item):
    """
    question：包含所有提供给模型的有用信息
    """
    db_id = str(item.get("db_id", "")).strip()
    difficulty = str(item.get("difficulty", "")).strip()
    question_text = str(item.get("question", "")).strip()
    evidence = str(item.get("evidence", "")).strip()

    question = (
        "You are given a natural language question and database context. "
        "Write the correct SQL query.\n\n"
        f"Database ID: {db_id}\n"
        f"Difficulty: {difficulty}\n\n"
        "=== Question ===\n"
        f"{question_text}\n\n"
    )

    if evidence:
        question += (
            "=== Evidence / Context ===\n"
            f"{evidence}\n\n"
        )

    question += "Task: Output the correct SQL query."
    return question


def build_answer(item):
    """
    answer：参考答案 SQL
    """
    return str(item.get("SQL", "")).strip()


def build_id(item, idx):
    """
    id：优先使用 question_id，否则 fallback
    """
    qid = item.get("question_id", None)
    if qid is not None:
        return str(qid)
    return f"sample_{idx}"


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
        description="Convert text-to-SQL JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
