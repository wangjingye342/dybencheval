import json
import argparse
from pathlib import Path


def build_question(record: dict, input_fields=None) -> str:
    """
    将 record 中多个字段拼接成一个 question 字段。
    如果 input_fields 为 None，则自动使用除 answer_field 之外的所有字段。
    """
    parts = []
    for field in input_fields:
        value = record.get(field, "")
        if value is None:
            value = ""
        value = str(value).strip()
        if value:
            parts.append(f"{field}:\n{value}")
    return "\n\n".join(parts).strip()


def convert_jsonl(input_path: str, output_path: str,
                  answer_field: str = "abstract",
                  input_fields=None,
                  id_field=None):
    """
    将 JSONL 转换为训练格式 JSONL: {id, question, answer}

    - answer_field: 指定哪个字段作为答案
    - input_fields: 指定哪些字段拼接到 question（不指定则自动选取）
    - id_field: 如果原始数据中有 id 字段可指定，否则自动用行号生成
    """

    input_path = Path(input_path)
    output_path = Path(output_path)

    assert input_path.exists(), f"输入文件不存在: {input_path}"

    converted = 0
    skipped = 0

    with input_path.open("r", encoding="utf-8") as fin, output_path.open("w", encoding="utf-8") as fout:
        for idx, line in enumerate(fin):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue

            # 生成 id
            if id_field and id_field in record:
                new_id = str(record[id_field])
            else:
                new_id = str(idx)

            # 自动决定用于 question 的字段
            if input_fields is None:
                # 默认：除答案字段外的所有字段都拼进 question
                input_fields_auto = [k for k in record.keys() if k != answer_field]
                question = build_question(record, input_fields_auto)
            else:
                question = build_question(record, input_fields)

            # answer
            answer = record.get(answer_field, "")
            if answer is None:
                answer = ""
            answer = str(answer).strip()

            # 如果 question 或 answer 为空，可以选择跳过
            if not question or not answer:
                skipped += 1
                continue

            new_record = {
                "id": new_id,
                "question": question,
                "answer": answer
            }

            fout.write(json.dumps(new_record, ensure_ascii=False) + "\n")
            converted += 1

    print(f"✅ 转换完成: {converted} 条写入 {output_path}")
    print(f"⚠️ 跳过记录: {skipped} 条（空行 / JSON错误 / question或answer为空）")


def main():
    parser = argparse.ArgumentParser(description="Convert jsonl dataset to {id, question, answer} format.")
    parser.add_argument("--input", required=True, help="Input jsonl file path")
    parser.add_argument("--output", required=True, help="Output jsonl file path")

    # 可选参数：如果你未来字段名变了可直接改命令行参数
    parser.add_argument("--answer_field", default="abstract", help="Which field is used as answer")
    parser.add_argument("--id_field", default=None, help="Which field is used as id (optional)")
    parser.add_argument("--input_fields", default=None,
                        help="Comma-separated list of fields used to build question (optional)")

    args = parser.parse_args()

    # 解析 input_fields
    if args.input_fields:
        input_fields = [f.strip() for f in args.input_fields.split(",") if f.strip()]
    else:
        input_fields = None

    convert_jsonl(
        input_path=args.input,
        output_path=args.output,
        answer_field=args.answer_field,
        input_fields=input_fields,
        id_field=args.id_field
    )


if __name__ == "__main__":
    main()
