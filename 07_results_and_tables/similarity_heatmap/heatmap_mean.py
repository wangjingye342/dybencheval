import json
import numpy as np
import csv
from collections import defaultdict
from pathlib import Path


def cosine_similarity(vec_a, vec_b):
    """计算两个向量的余弦相似度"""
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return np.dot(vec_a, vec_b) / (norm_a * norm_b)


def main():
    # ======================
    # 1. 配置文件路径
    # ======================
    base_dir = Path("D:/STUDY/2026-project1/project1/rebuttal/heatmap/分别embedding")
    input_file = base_dir / "all_datasets_embedded_new.jsonl"
    output_csv = base_dir / "new_mean_similarity.csv"

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
            cell_embeddings[(data["domain"], data["task"])].append(np.array(data["text_embedding"]))

    if not cell_embeddings:
        print("未加载到任何有效数据，请检查文件格式。")
        return

    # ======================
    # 3. 计算每个独立 Cell 的自身均值
    # ======================
    cell_mean_embs = {}
    for cell, embs in cell_embeddings.items():
        cell_mean_embs[cell] = np.mean(embs, axis=0)

    # ======================
    # 4. 匹配空缺 Cell、计算并过滤对比范围
    # ======================
    results = []
    actual_cells = list(cell_embeddings.keys())

    for target_domain_kw, target_task_kw in incomplete_targets:
        matched_domain = next((d for d, t in actual_cells if
                               target_domain_kw.lower() in d.lower() or target_domain_kw.replace(" ", "") in d),
                              target_domain_kw)
        matched_task = next((t for d, t in actual_cells if target_task_kw in t), target_task_kw)

        target_cell = (matched_domain, matched_task)

        # 收集同行 (同 domain) 或 同列 (同 task) 的所有数据集的 embeddings 作为该空缺 cell 的特征融合
        related_embs = []
        for e_cell, embs in cell_embeddings.items():
            if e_cell[0] == matched_domain or e_cell[1] == matched_task:
                related_embs.extend(embs)

        if not related_embs:
            continue

        target_fusion_mean = np.mean(related_embs, axis=0)

        sims = []
        for e_cell, e_mean_emb in cell_mean_embs.items():
            if e_cell == target_cell:
                continue

            # 【核心修改点】：仅对比同行（同 domain）或同列（同 task）的其它 cell
            if e_cell[0] == matched_domain or e_cell[1] == matched_task:
                cos_sim = cosine_similarity(target_fusion_mean, e_mean_emb)
                sims.append((e_cell, cos_sim))

        sims.sort(key=lambda x: x[1], reverse=True)
        results.append((target_cell, sims))

    # ======================
    # 5. 打印并保存到 CSV 表格
    # ======================
    print("\n| Dataset | Most Similar Datasets Based on Mean Embeddings (Row/Col Only) |")
    print("| :--- | :--- |")

    with output_csv.open("w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Dataset (Missing Cell)", "Most Similar Datasets Based on Mean Embeddings (Row/Col Only)"])

        for target_cell, sims in results:
            cell_name = f"({target_cell[0]}, {target_cell[1]})"
            # 限制输出前 5 个最相似的同行/同列单元格
            sims_str_list = [f"({e_cell[0]}, {e_cell[1]}) {sim:.4f}" for e_cell, sim in sims[:5]]
            sims_str = ", ".join(sims_str_list)

            print(f"| {cell_name} | {sims_str} |")
            writer.writerow([cell_name, sims_str])

    print(f"\n✅ 处理完成！均值算法结果已保存至：{output_csv}")


if __name__ == "__main__":
    main()