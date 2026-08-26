import json
import argparse
from pathlib import Path


def format_choices(choices):
    """
    将 choices list 变成可读文本（A/B/C/D…）
    """
    if not choices:
        return ""
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lines = []
    for i, c in enumerate(choices):
        label = letters[i] if i < len(letters) else f"Option{i}"
        lines.append(f"{label}. {c}")
    return "\n".join(lines)


def build_question(item):
    """
    question：包含所有对模型有用的信息
    """
    scenario = str(item.get("target_scenario", "")).strip()
    task = str(item.get("target_task", "")).strip()
    subject = str(item.get("subject", "")).strip()
    q_text = str(item.get("question", "")).strip()
    choices = item.get("choices", [])

    question = (
        "You are given a multiple-choice question. Choose the correct option.\n\n"
        f"Scenario: {scenario}\n"
        f"Task: {task}\n"
        f"Subject: {subject}\n\n"
        "=== Question ===\n"
        f"{q_text}\n\n"
        "=== Choices ===\n"
        f"{format_choices(choices)}\n\n"
        "Task: Provide the correct answer option."
    )
    return question


def build_answer(item):
    """
    answer：将索引映射为选项文本（推荐）
    """
    choices = item.get("choices", [])
    ans_idx = item.get("answer", None)

    if isinstance(ans_idx, int) and 0 <= ans_idx < len(choices):
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        label = letters[ans_idx] if ans_idx < len(letters) else str(ans_idx)
        return f"{label}. {choices[ans_idx]}"

    # fallback：无法映射时直接输出原始 answer
    return str(ans_idx)


def build_id(item, idx):
    """
    id：优先 my_generated_id，否则 fallback
    """
    gid = item.get("my_generated_id", None)
    if gid is not None:
        return str(gid)
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
        description="Convert multiple-choice JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
