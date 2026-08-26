import json
import numpy as np
from pathlib import Path
from tqdm import tqdm

# ======================
# 1. 目录配置
# ======================

# 这里是你上一步跑出来的 embedding 结果目录
INPUT_DIRECTORY = Path("D:/STUDY/2026-project1/project1/main_work/计算指标/1/re_embedding")
# 新的输出目录，用于保存带有相似度得分的数据
OUTPUT_DIRECTORY = Path("D:/STUDY/2026-project1/project1/main_work/计算指标/1/scored_data")


# ======================
# 2. 余弦相似度计算函数
# ======================

def compute_cosine_similarity(vec1: list, vec2: list) -> float:
    """使用 numpy 计算两个向量的余弦相似度"""
    # 转换为 numpy 数组
    v1 = np.array(vec1)
    v2 = np.array(vec2)

    # 计算 L2 范数（向量长度）
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    # 防止除以 0 的极端情况
    if norm1 == 0 or norm2 == 0:
        return 0.0

    # 计算点积并除以两个向量的范数之积
    similarity = np.dot(v1, v2) / (norm1 * norm2)

    # 浮点数精度问题可能会导致结果略微超出 [-1.0, 1.0] 范围，进行裁剪限制
    return float(np.clip(similarity, -1.0, 1.0))


# ======================
# 3. 数据处理主逻辑
# ======================

def process_dataset(input_path: Path, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 用于统计该数据集的平均相似度
    total_similarity = 0.0
    valid_count = 0

    with input_path.open("r", encoding="utf-8") as fin, \
            output_path.open("w", encoding="utf-8") as fout:

        lines = fin.readlines()

        for line in tqdm(
                lines,
                desc=f"Scoring {input_path.name}",
                unit="samples",
                dynamic_ncols=True
        ):
            if not line.strip():
                continue

            sample = json.loads(line)

            # 提取 embedding
            seed_emb = sample.get("seed_text_embedding")
            response_emb = sample.get("response_text_embedding")

            # 确保两个 embedding 都存在且合法
            if seed_emb and response_emb:
                score = compute_cosine_similarity(seed_emb, response_emb)

                # 将计算结果保存到原字典中
                sample["cosine_similarity"] = score

                total_similarity += score
                valid_count += 1
            else:
                # 如果没有 embedding 数据，默认给一个 None 标识
                sample["cosine_similarity"] = None

            # 写入新文件
            fout.write(json.dumps(sample, ensure_ascii=False) + "\n")

    # 打印该文件的简要统计信息
    if valid_count > 0:
        avg_score = total_similarity / valid_count
        print(f" -> [{input_path.name}] 平均相似度: {avg_score:.4f} (共 {valid_count} 条)")


# ======================
# 4. 总体流程
# ======================

def main():
    # 扫描目录下所有的 jsonl 文件
    jsonl_files = list(INPUT_DIRECTORY.glob("*.jsonl"))

    if not jsonl_files:
        print(f"未在 {INPUT_DIRECTORY} 中找到数据文件。")
        return

    for input_path in jsonl_files:
        # 如果你只想处理特定后缀的文件，可以取消下一行的注释
        # if not input_path.name.endswith("_embedded.jsonl"): continue

        output_path = OUTPUT_DIRECTORY / f"{input_path.stem}_scored.jsonl"
        process_dataset(input_path, output_path)

    print("\n所有相似度计算完毕！")


if __name__ == "__main__":
    main()