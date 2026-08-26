import json
import argparse
from pathlib import Path


def format_analysis(analysis):
    """
    将 analysis dict 转为文本，方便放入 question
    """
    if not analysis:
        return ""
    if isinstance(analysis, dict):
        return "\n".join([f"{k}: {v}" for k, v in analysis.items()])
    return str(analysis)


def build_question(item):
    """
    question：包含所有提供给模型的有用信息
    """
    scenario = str(item.get("target_scenario", "")).strip()
    task = str(item.get("target_task", "")).strip()
    role = str(item.get("role", "")).strip()
    context = str(item.get("context", "")).strip()
    user_query = str(item.get("user_query", "")).strip()
    analysis = item.get("analysis", {})

    question = (
        "You are an assistant. Use the given scenario, task, and context to answer the user query.\n\n"
        f"Scenario: {scenario}\n"
        f"Task: {task}\n"
        f"Role: {role}\n\n"
        "=== Context ===\n"
        f"{context}\n\n"
        "=== User Query ===\n"
        f"{user_query}\n\n"
    )

    # analysis 可选：如果你不想模型看到，可删掉这段
    if analysis:
        question += (
            "=== Analysis Metadata (Optional) ===\n"
            f"{format_analysis(analysis)}\n\n"
        )

    question += "Task: Write the best assistant response."
    return question


def build_answer(item):
    """
    answer：参考答案 generated_response
    """
    return str(item.get("generated_response", "")).strip()


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
        description="Convert assistant generation JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
