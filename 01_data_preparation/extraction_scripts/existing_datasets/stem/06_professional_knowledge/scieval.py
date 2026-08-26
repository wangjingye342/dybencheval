import json
import argparse
from pathlib import Path


def build_question(item):
    """
    question：包含所有对模型有用的信息
    """
    task_name = str(item.get("task_name", "")).strip()
    category = str(item.get("category", "")).strip()
    topic = str(item.get("topic", "")).strip() if item.get("topic") is not None else ""
    ability = str(item.get("ability", "")).strip()
    qtype = str(item.get("type", "")).strip()

    prompt = str(item.get("prompt", "")).strip()
    cot_prompt = str(item.get("cot_prompt", "")).strip()
    question_text = str(item.get("question", "")).strip()

    question = (
        "You are given a task instruction and a question. Please answer based on the instruction.\n\n"
        f"Task Name: {task_name}\n"
        f"Category: {category}\n"
        f"Topic: {topic}\n"
        f"Ability: {ability}\n"
        f"Type: {qtype}\n\n"
        "=== Instruction Prompt ===\n"
        f"{prompt}\n\n"
        "=== CoT Prompt (Optional) ===\n"
        f"{cot_prompt}\n\n"
        "=== Question ===\n"
        f"{question_text}\n\n"
        "Task: Provide the best correct answer."
    )
    return question


def build_answer(item):
    """
    answer：保留原始 list，转换成 JSON 字符串
    （方便你后续改成只取第一个答案）
    """
    ans = item.get("answer", [])
    return json.dumps(ans, ensure_ascii=False)


def build_id(idx, item):
    """
    id：默认行号；也可以用 task_name + idx 让更稳定
    """
    task_name = str(item.get("task_name", "task")).strip()
    return f"{task_name}_{idx}"


def convert_dataset(input_file, output_file):
    input_path = Path(input_file)
    output_path = Path(output_file)

    results = []
    with input_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            item = json.loads(line)

            sample_id = build_id(idx, item)
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
        description="Convert multi-answer JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
