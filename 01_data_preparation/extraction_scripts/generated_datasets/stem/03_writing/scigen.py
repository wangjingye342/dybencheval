import json
import argparse
from pathlib import Path


def to_markdown_table(columns, rows, max_rows=30):
    """
    把表格列名 + 行值转成 Markdown 表格
    max_rows 用于避免表格太大
    """
    if not columns:
        return ""

    # 限制行数避免过长
    rows = rows[:max_rows] if isinstance(rows, list) else []

    header = "| " + " | ".join([str(c) for c in columns]) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body_lines = []
    for r in rows:
        if isinstance(r, list):
            body_lines.append("| " + " | ".join([str(x) for x in r]) + " |")
        else:
            body_lines.append("| " + str(r) + " |")

    return "\n".join([header, sep] + body_lines)


def build_question(item, table_format="markdown"):
    """
    question：包含所有对模型有用的信息
    table_format: markdown / json
    """
    paper = str(item.get("paper", "")).strip()
    paper_id = str(item.get("paper_id", "")).strip()
    caption = str(item.get("table_caption", "")).strip()
    columns = item.get("table_column_names", [])
    values = item.get("table_content_values", [])
    text = str(item.get("text", "")).strip()

    # 生成 table 表示
    if table_format == "json":
        table_repr = json.dumps(
            {"columns": columns, "values": values},
            ensure_ascii=False,
            indent=2
        )
    else:
        table_repr = to_markdown_table(columns, values)

    question = (
        "You are given a scientific paper table and related context. "
        "Generate a descriptive paragraph that explains the table content.\n\n"
        f"Paper: {paper}\n"
        f"Paper ID: {paper_id}\n\n"
        "=== Table Caption ===\n"
        f"{caption}\n\n"
        "=== Table ===\n"
        f"{table_repr}\n\n"
        "=== Related Context Text (Optional) ===\n"
        f"{text}\n\n"
        "Task: Write a clear explanation/summary of the table."
    )

    return question


def build_answer(item):
    """
    answer：参考答案 text（论文中与表格对应的描述）
    """
    return str(item.get("text", "")).strip()


def build_id(item, idx):
    """
    id：优先 paper_id，否则 fallback
    如果 paper_id 可能重复，建议拼 idx
    """
    pid = str(item.get("paper_id", "")).strip()
    if pid:
        return f"{pid}_{idx}"
    return f"sample_{idx}"


def convert_dataset(input_file, output_file, table_format="markdown"):
    input_path = Path(input_file)
    output_path = Path(output_file)

    results = []
    with input_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            item = json.loads(line)

            results.append({
                "id": build_id(item, idx),
                "question": build_question(item, table_format=table_format),
                "answer": build_answer(item)
            })

    with output_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Converted {len(results)} samples -> {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert table-to-text JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")
    parser.add_argument(
        "--table_format",
        default="markdown",
        choices=["markdown", "json"],
        help="How to format the table in question (markdown/json)"
    )

    args = parser.parse_args()
    convert_dataset(args.input, args.output, table_format=args.table_format)


if __name__ == "__main__":
    main()
