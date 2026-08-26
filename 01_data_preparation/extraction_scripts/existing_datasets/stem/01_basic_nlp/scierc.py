import json
import argparse
from pathlib import Path


def tokens_to_text(sentences):
    """
    将 sentences (二维 token list) 拼接成连续文本
    """
    return "\n".join([" ".join(sent) for sent in sentences])


def format_clusters(clusters):
    """
    将 clusters 转换为可读格式（仍保留 span 信息）
    clusters: list of entity clusters
    """
    cluster_strs = []
    for idx, cluster in enumerate(clusters):
        spans = [f"{span}" for span in cluster]
        cluster_strs.append(f"Cluster {idx}: " + "; ".join(spans))
    return "\n".join(cluster_strs)


def format_relations(relations):
    """
    将 relations 转换为可读格式
    relations: list[list[relation]]
    relation: [start1, end1, start2, end2, label]
    """
    rel_strs = []
    for sent_idx, rel_list in enumerate(relations):
        for rel in rel_list:
            if len(rel) == 5:
                s1, e1, s2, e2, label = rel
                rel_strs.append(
                    f"Sent {sent_idx}: ({s1}-{e1}) --{label}--> ({s2}-{e2})"
                )
            else:
                rel_strs.append(f"Sent {sent_idx}: {rel}")
    return "\n".join(rel_strs)


def build_question(item):
    """
    question 中包含所有对模型有用的信息：
    - 原文文本
    - clusters
    - relations
    """
    doc_text = tokens_to_text(item.get("sentences", []))
    clusters_info = format_clusters(item.get("clusters", []))
    relations_info = format_relations(item.get("relations", []))

    question = (
        "You are given a document with tokenized sentences, entity clusters, and relations.\n\n"
        "=== Document Text ===\n"
        f"{doc_text}\n\n"
        "=== Entity Clusters (spans) ===\n"
        f"{clusters_info}\n\n"
        "=== Relations (spans and labels) ===\n"
        f"{relations_info}\n\n"
        "Task: Predict or reason about relations based on the given context."
    )
    return question


def build_answer(item):
    """
    answer 为参考答案：
    - 默认使用 relations 作为答案
    - 你也可以在此改为 clusters 或其他字段
    """
    return json.dumps(item.get("relations", []), ensure_ascii=False)


def convert_dataset(input_file, output_file):
    input_path = Path(input_file)
    output_path = Path(output_file)

    results = []
    with input_path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            item = json.loads(line)

            # id 优先使用 doc_key，否则 fallback 为行号
            sample_id = item.get("doc_key", f"sample_{i}")

            question = build_question(item)
            answer = build_answer(item)

            results.append({
                "id": sample_id,
                "question": question,
                "answer": answer
            })

    # 写出为 JSONL
    with output_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Converted {len(results)} samples -> {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Convert JSONL dataset into training format (id/question/answer)")
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
