import json
import numpy as np
import csv
from collections import defaultdict
from pathlib import Path


def pairwise_cosine_similarity_mean(embs_a, embs_b):
    """通过矩阵乘法加速逐条对比的过程"""
    arr_a, arr_b = np.array(embs_a), np.array(embs_b)
    norm_a = np.linalg.norm(arr_a, axis=1, keepdims=True)
    norm_b = np.linalg.norm(arr_b, axis=1, keepdims=True)
    norm_a[norm_a == 0] = 1e-10
    norm_b[norm_b == 0] = 1e-10
    sim_matrix = np.dot(arr_a / norm_a, (arr_b / norm_b).T)
    return float(np.mean(sim_matrix))


def main():
    # ======================
    # 1. 配置文件路径
    # ======================
    base_dir = Path("./external/embeddings")
    input_file = base_dir / "all_datasets_embedded_new.jsonl"
    output_csv = base_dir / "new_pairwise_similarity.csv"

    if not input_file.exists():
        print(f"找不到文件: {input_file}")
        return

    incomplete_targets = [
        ("STEM", "写作能力"),
        ("Humanity", "角色扮演"),
        ("Humanity", "代码生成"),
        ("SocialScience", "基本NLP任务"),
        ("SocialScience", "写作能力"),
        ("SocialScience", "角色扮演"),
        ("SocialScience", "代码生成"),
        ("Other", "专业知识")
    ]

    print("正在加载数据并提取 Embedding，请稍候...")
    cell_embeddings = defaultdict(list)

    # ======================
    # 2. 读取数据并建立网格
    # ======================
    with input_file.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            data = json.loads(line)
            cell_embeddings[(data["domain"], data["task"])].append(data["text_embedding"])

    if not cell_embeddings:
        print("未加载到任何有效数据，请检查文件格式。")
        return

    # ======================
    # 3. 匹配空缺 Cell、执行 Pairwise 计算并过滤
    # ======================
    results = []
    actual_cells = list(cell_embeddings.keys())

    print("开始进行 Pairwise similarity计算 (这可能需要一点时间)...")

    for target_domain_kw, target_task_kw in incomplete_targets:
        matched_domain = next((d for d, t in actual_cells if
                               target_domain_kw.lower() in d.lower() or target_domain_kw.replace(" ", "") in d),
                              target_domain_kw)
        matched_task = next((t for d, t in actual_cells if target_task_kw in t), target_task_kw)

        target_cell = (matched_domain, matched_task)

        # 收集同行 (同 domain) 或 同列 (同 task) 的所有数据集的 embeddings
        related_embs = []
        for e_cell, embs in cell_embeddings.items():
            if e_cell[0] == matched_domain or e_cell[1] == matched_task:
                related_embs.extend(embs)

        if not related_embs:
            continue

        sims = []
        for e_cell, embs in cell_embeddings.items():
            if e_cell == target_cell:
                continue

            # 【核心修改点】：仅对比同行（同 domain）或同列（同 task）的其它 cell
            if e_cell[0] == matched_domain or e_cell[1] == matched_task:
                avg_pairwise_sim = pairwise_cosine_similarity_mean(related_embs, embs)
                sims.append((e_cell, avg_pairwise_sim))

        sims.sort(key=lambda x: x[1], reverse=True)
        results.append((target_cell, sims))

    # ======================
    # 4. 打印并保存到 CSV 表格
    # ======================
    print("\n| Dataset | Most Similar Datasets Based on Pairwise Embeddings (Row/Col Only) |")
    print("| :--- | :--- |")

    with output_csv.open("w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Dataset (Missing Cell)", "Most Similar Datasets Based on Pairwise Embeddings (Row/Col Only)"])

        for target_cell, sims in results:
            cell_name = f"({target_cell[0]}, {target_cell[1]})"
            sims_str_list = [f"({e_cell[0]}, {e_cell[1]}) {sim:.4f}" for e_cell, sim in sims[:5]]
            sims_str = ", ".join(sims_str_list)

            print(f"| {cell_name} | {sims_str} |")
            writer.writerow([cell_name, sims_str])

    print(f"\n✅ 处理完成！Pairwise 算法结果已保存至：{output_csv}")


if __name__ == "__main__":
    main()