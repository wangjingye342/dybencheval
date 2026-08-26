import os
import json
import torch
from vendi_score import text_utils

# --- 配置区域 ---
DATASET_DIR = "./results"  # 替换为你的目录路径
OUTPUT_FILE = "./vendi_scores_2_results.json"
MODEL_PATH = "D:/STUDY/2026-project1/project1/rebuttal/unsup-simcse-bert-base-uncased"
BATCH_SIZE = 128


def calculate_scores_for_directory():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"当前使用的计算设备: {device}")

    results = {}
    if not os.path.exists(DATASET_DIR):
        print(f"错误: 目录 '{DATASET_DIR}' 不存在。")
        return

    for filename in os.listdir(DATASET_DIR):
        filepath = os.path.join(DATASET_DIR, filename)
        if not os.path.isfile(filepath):
            continue

        responses = []

        # 读取并严格校验数据
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if filename.endswith(".jsonl"):
                    for line in f:
                        if not line.strip(): continue
                        data = json.loads(line)
                        if "response" in data and isinstance(data["response"], str) and data["response"].strip():
                            responses.append(data["response"])

                elif filename.endswith(".json"):
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and "response" in item and isinstance(item["response"], str) and \
                                    item["response"].strip():
                                responses.append(item["response"])
        except Exception as e:
            print(f"读取文件 {filename} 时出错: {e}")
            continue

        if len(responses) < 2:
            print(f"跳过 {filename}: 有效数据量不足（{len(responses)}条），无法计算多样性得分。")
            continue

        print(f"正在处理 [{filename}]，共提取到 {len(responses)} 条有效 response...")

        # 动态调整 Batch Size 防报错
        safe_batch_size = BATCH_SIZE
        while len(responses) % safe_batch_size == 1:
            safe_batch_size -= 1

        if safe_batch_size != BATCH_SIZE:
            print(f"  * 触发防报错机制: 将 Batch Size 临时从 {BATCH_SIZE} 调整为 {safe_batch_size}")

        # 计算 Vendi Score
        try:
            score = text_utils.embedding_vendi_score(
                responses,
                model_path=MODEL_PATH,
                device=device,
                batch_size=safe_batch_size
            )

            # 【修复点】：使用 float() 将 NumPy/PyTorch float32 转换为原生 Python float
            results[filename] = float(score)
            print(f"--> {filename} 的 Vendi Score: {float(score):.4f}")

            if device == "cuda":
                torch.cuda.empty_cache()

        except Exception as e:
            print(f"计算 {filename} 的 Vendi Score 时发生错误: {e}")

    # 保存结果
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        print(f"\n所有计算完成！结果已成功保存至: {OUTPUT_FILE}")
    except Exception as e:
        print(f"保存结果文件时出错: {e}")


if __name__ == "__main__":
    calculate_scores_for_directory()