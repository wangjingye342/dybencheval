import json
import argparse
from pathlib import Path


def build_question(item):
    """
    question 包含所有提供给模型的有用信息
    """
    age = item.get("AGE", "")
    sex = item.get("SEX", "")
    race = item.get("RACE", "")
    initial = item.get("INITIAL_EVIDENCE", "").strip()
    evidences = item.get("EVIDENCES", "").strip()
    diff_diag = item.get("DIFFERENTIAL_DIAGNOSIS", "").strip()

    question = (
        "You are given a medical case. Based on the patient information and evidences, "
        "predict the most likely pathology (final diagnosis).\n\n"
        f"Age: {age}\n"
        f"Sex: {sex}\n"
        f"Race: {race}\n\n"
        "=== Initial Evidence ===\n"
        f"{initial}\n\n"
        "=== Additional Evidences ===\n"
        f"{evidences}\n\n"
        "=== Differential Diagnosis (candidate conditions) ===\n"
        f"{diff_diag}\n\n"
        "Task: Provide the most likely final pathology diagnosis."
    )
    return question


def build_answer(item):
    """
    answer 为参考答案：最终诊断 PATHOLOGY
    """
    return str(item.get("PATHOLOGY", "")).strip()


def build_id(idx):
    """
    id 生成策略：行号
    """
    return f"case_{idx}"


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
        description="Convert medical diagnosis JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
