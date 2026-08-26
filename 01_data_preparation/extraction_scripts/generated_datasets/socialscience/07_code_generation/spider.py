import json
import argparse
from pathlib import Path


def build_question(item, include_question_toks=False):
    """
    question：包含所有给模型的有用信息
    """
    db_id = str(item.get("db_id", "")).strip()
    q = str(item.get("question", "")).strip()
    q_toks = item.get("question_toks", [])

    question = (
        "You are given a natural language question and a database id. "
        "Write the correct SQL query.\n\n"
        f"Database ID: {db_id}\n\n"
        "=== Question ===\n"
        f"{q}\n\n"
    )

    if include_question_toks and q_toks:
        question += (
            "=== Question Tokens (Optional) ===\n"
            f"{' '.join([str(x) for x in q_toks])}\n\n"
        )

    question += "Task: Output the SQL query."
    return question


def build_answer(item, structured=True):
    """
    answer：
    - structured=True: 输出 {"query": ..., "sql": ...}
    - structured=False: 只输出 query
    """
    query = str(item.get("query", "")).strip()
    sql_ast = item.get("sql", {})

    if structured:
        return json.dumps({"query": query, "sql": sql_ast}, ensure_ascii=False)
    return query


def build_id(item, idx):
    """
    id：db_id + 行号
    """
    db_id = str(item.get("db_id", "db")).strip()
    return f"{db_id}_{idx}"


def convert_dataset(input_file, output_file, include_question_toks=False, structured_answer=True):
    input_path = Path(input_file)
    output_path = Path(output_file)

    results = []
    with input_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            item = json.loads(line)

            results.append({
                "id": build_id(item, idx),
                "question": build_question(item, include_question_toks=include_question_toks),
                "answer": build_answer(item, structured=structured_answer)
            })

    with output_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Converted {len(results)} samples -> {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert Spider-like Text-to-SQL JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")
    parser.add_argument(
        "--include_question_toks",
        action="store_true",
        help="Include question_toks into question (default False)"
    )
    parser.add_argument(
        "--simple_answer",
        action="store_true",
        help="If set, answer will be only query string (default outputs structured JSON with query+sql)"
    )

    args = parser.parse_args()
    structured_answer = not args.simple_answer

    convert_dataset(
        args.input,
        args.output,
        include_question_toks=args.include_question_toks,
        structured_answer=structured_answer
    )


if __name__ == "__main__":
    main()
