import json
import argparse
from pathlib import Path


def build_question(item):
    """
    question 包含所有提供给模型的有用信息
    """
    qid = item.get("qid", "")
    scenario = item.get("scenario", "")
    question_text = item.get("question", "").strip()
    student_profile = item.get("student_profile", "").strip()
    student_wrong = item.get("student_incorrect_solution", "").strip()
    teacher_confusion = item.get("teacher_described_confusion", "").strip()
    conversation = item.get("conversation", "").strip()

    self_correctness = item.get("self-correctness", "").strip()
    typical_confusion = item.get("self-typical-confusion", "")
    typical_interactions = item.get("self-typical-interactions", "")

    question = (
        "You are a helpful teacher assistant. You are given a student profile, the original question, "
        "the student's incorrect solution, and discussion context. Your task is to provide the correct answer.\n\n"
        f"QID: {qid}\n"
        f"Scenario: {scenario}\n\n"
        "=== Student Profile ===\n"
        f"{student_profile}\n\n"
        "=== Question ===\n"
        f"{question_text}\n\n"
        "=== Student Incorrect Solution ===\n"
        f"{student_wrong}\n\n"
        "=== Teacher-described Confusion ===\n"
        f"{teacher_confusion}\n\n"
        "=== Conversation Context ===\n"
        f"{conversation}\n\n"
        "=== Self-report Features ===\n"
        f"Self-correctness: {self_correctness}\n"
        f"Typical confusion score: {typical_confusion}\n"
        f"Typical interactions score: {typical_interactions}\n\n"
        "Task: Provide the correct final answer."
    )
    return question


def build_answer(item):
    """
    answer 为参考答案：ground_truth
    """
    return str(item.get("ground_truth", "")).strip()


def build_id(item, idx):
    """
    id 生成策略：
    - 优先用 qid
    - fallback 行号
    """
    qid = item.get("qid", None)
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
        description="Convert student-teacher JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
