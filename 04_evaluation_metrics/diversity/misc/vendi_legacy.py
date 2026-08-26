import os
import json
import torch
from vendi_score import text_utils

# ================= 配置区域 =================
# 存放数据集的实际文件夹相对路径
DATA_DIR = "./results"
# 结果保存的文件名
OUTPUT_FILE = "simcse_vendi_scores_gpu.json"
# 使用的本地模型路径
MODEL_PATH = "D:/STUDY/2026-project1/project1/rebuttal/unsup-simcse-bert-base-uncased"

# 动态检测硬件以使用 GPU 加速
# 优先使用 CUDA (NVIDIA GPU)，其次是 MPS (Mac Apple Silicon)，最后回退到 CPU
if torch.cuda.is_available():
    DEVICE = "cuda"
else:
    DEVICE = "cpu"

# ============================================

def load_responses(filepath):
    """
    从文件中加载所有的 response 字段，并确保提取出非空字符串。
    兼容 JSONL 和 标准 JSON 列表 格式。
    """
    responses = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # 1. 尝试作为完整的 JSON 列表读取
            try:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        raw_resp = item.get("response")
                        if isinstance(raw_resp, str) and raw_resp.strip():
                            responses.append(raw_resp.strip())
                    return responses
            except json.JSONDecodeError:
                # 若失败说明可能是 JSONL 格式，将文件指针拨回开头
                f.seek(0)

            # 2. 按照 JSONL 格式逐行读取
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        raw_resp = data.get("response")
                        if isinstance(raw_resp, str) and raw_resp.strip():
                            responses.append(raw_resp.strip())
                    except json.JSONDecodeError:
                        continue  # 忽略格式损坏的行
    except Exception as e:
        print(f"读取文件 {filepath} 时出错: {e}")

    return responses


def main():
    if not os.path.exists(DATA_DIR):
        print(f"错误: 找不到目录 '{DATA_DIR}'")
        return

    results = {}

    print(f"当前计算设备: {DEVICE.upper()}")
    print(f"开始遍历目录: {DATA_DIR}\n" + "-" * 40)

    for filename in os.listdir(DATA_DIR):
        filepath = os.path.join(DATA_DIR, filename)

        if os.path.isdir(filepath):
            continue

        print(f"正在处理: {filename}")
        responses = load_responses(filepath)

        if not responses:
            print(f"⚠️ 警告: 在 {filename} 中未找到包含有效 'response' 的数据，已跳过。\n")
            continue

        print(f"已提取 {len(responses)} 条数据，正在计算 SimCSE Vendi Score...")

        try:
            # === 核心修复逻辑：动态调整 batch_size 避开降维 Bug ===
            # 注意：既然使用了 GPU，如果显存（VRAM）充裕，你可以尝试将 safe_batch_size 调大（如 32, 64 等）以进一步提速。
            safe_batch_size = 16
            if len(responses) % safe_batch_size == 1:
                safe_batch_size = 15

            # 计算 Vendi Score
            simcse_vs = text_utils.embedding_vendi_score(
                responses,
                model_path=MODEL_PATH,
                device=DEVICE,
                batch_size=safe_batch_size
            )

            results[filename] = float(simcse_vs)
            print(f"✅ 完成！得分: {simcse_vs:.4f}\n")

        except Exception as e:
            print(f"❌ 计算 {filename} 时发生错误: {e}\n")

    print("-" * 40)
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        print(f"🎉 所有计算已完成！结果已成功保存至: {OUTPUT_FILE}")
    except Exception as e:
        print(f"保存结果文件时出错: {e}")


if __name__ == "__main__":
    main()