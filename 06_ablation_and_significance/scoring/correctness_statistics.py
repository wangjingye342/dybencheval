import os
import json
import glob

# ================= 配置区域 =================
# 输入目录 (你提供的processed目录)
INPUT_DIR = "D:/STUDY/2026-project1/project1/main_work/scripts/后补实验/评估指标/3/results_correctness_processed_clean"
# 统计结果保存路径 (可选)
OUTPUT_SUMMARY_FILE = os.path.join(INPUT_DIR, "coherence_score_summary.json")


# ================= 核心逻辑 =================

def calculate_coherence_scores():
    # 1. 检查目录是否存在
    if not os.path.exists(INPUT_DIR):
        print(f"错误: 找不到目录 {INPUT_DIR}")
        return

    # 2. 获取所有 jsonl 文件
    files = glob.glob(os.path.join(INPUT_DIR, "*.jsonl"))
    if not files:
        print(f"在 {INPUT_DIR} 中未找到 .jsonl 文件")
        return

    # 按文件名排序，方便查看
    files.sort()

    summary_results = {}

    print(f"\n{'=' * 90}")
    print(f"{'File Name':<55} | {'Average Score':<15} | {'Sample Count':<10}")
    print(f"{'-' * 90}")

    for file_path in files:
        file_name = os.path.basename(file_path)
        scores = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        # 提取 eval_result
                        # 注意：这里假设 eval_result 已经是提取好的数字 (int/float)
                        # 如果是字符串 (例如 "8")，float() 会自动转换
                        score_val = data.get("eval_result")

                        if score_val is not None:
                            try:
                                # 强制转为浮点数进行计算
                                score = float(score_val)
                                scores.append(score)
                            except ValueError:
                                # 如果 eval_result 不是数字（比如是错误信息），则跳过
                                continue

                    except json.JSONDecodeError:
                        continue

            # 计算平均值
            if scores:
                avg_score = sum(scores) / len(scores)
                summary_results[file_name] = {
                    "average": avg_score,
                    "count": len(scores)
                }
                print(f"{file_name:<55} | {avg_score:.4f}          | {len(scores)}")
            else:
                summary_results[file_name] = {"average": 0, "count": 0}
                print(f"{file_name:<55} | {'N/A':<15} | 0")

        except Exception as e:
            print(f"处理文件 {file_name} 时出错: {e}")

    print(f"{'=' * 90}\n")

    # 保存统计结果到文件
    try:
        with open(OUTPUT_SUMMARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(summary_results, f, ensure_ascii=False, indent=4)
        print(f"统计结果已保存至: {OUTPUT_SUMMARY_FILE}")
    except Exception as e:
        print(f"保存统计文件失败: {e}")


if __name__ == "__main__":
    calculate_coherence_scores()