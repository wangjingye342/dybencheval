import json
import time
import re
import os
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm

# ======================
# 1. 配置区域
# ======================

# [安全提示] 建议将 Key 放入环境变量。
# 请在此处填入您真实的 API Key
API_KEY = os.environ.get("DYBENCH_API_KEY", "")
BASE_URL = "https://api.whatai.cc/v1"

MODEL_NAME = "qwen3-max"

INPUT_FILE = "./external/model_runs/constructed_prompts_temporary_augmentation.jsonl"


# ======================
# 2. 输出文件名构造
# ======================

def sanitize_model_name(name: str) -> str:
    return re.sub(r"[^\w\-]+", "_", name)


model_tag = sanitize_model_name(MODEL_NAME)

OUTPUT_FILE = Path(
    f"./external/model_runs/results/api_results_{model_tag}.jsonl"
)

# ======================
# 3. 初始化客户端
# ======================

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)


# ======================
# 4. 辅助函数：计算已处理行数
# ======================
def count_lines(filepath: Path) -> int:
    """计算文件已有行数，作为断点位置"""
    if not filepath.exists():
        return 0
    with open(filepath, "r", encoding="utf-8") as f:
        # 统计文件行数
        return sum(1 for _ in f)


# ======================
# 5. 主推理逻辑（带断点续传）
# ======================

def run_inference(input_file: str, output_file: Path):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print("正在统计输入文件总任务数...")
    # 1. 预统计总行数（只统计非空行）
    with open(input_file, "r", encoding="utf-8") as f:
        total_input_lines = sum(1 for line in f if line.strip())

    # 2. 获取断点位置（检查输出文件已有多少行）
    processed_count = count_lines(output_file)

    print(f"总任务数: {total_input_lines}")
    print(f"已完成数: {processed_count}")

    if processed_count >= total_input_lines:
        print("所有任务已完成，无需运行。")
        return

    # 3. 开始处理
    # 注意：输出文件使用 "a" (append) 模式，以追加写入
    with open(input_file, "r", encoding="utf-8") as fin, \
            open(output_file, "a", encoding="utf-8") as fout, \
            tqdm(total=total_input_lines, initial=processed_count, desc="Inference Progress", unit="sample") as pbar:

        valid_input_idx = 0  # 用于记录当前读取的是第几个有效输入行

        for line in fin:
            line = line.strip()
            if not line:
                continue

            # 这是一个有效行，计数器+1
            valid_input_idx += 1

            # === [核心修改] 断点跳过逻辑 ===
            # 如果当前行的序号 <= 已处理的行数，说明之前跑过了，直接跳过
            if valid_input_idx <= processed_count:
                continue

            # === 下面是正常的推理逻辑 ===

            # 1. 解析原始数据行
            try:
                original_data = json.loads(line)
            except json.JSONDecodeError:
                print(f"[WARN] JSON decode error at line {valid_input_idx}, skipping.")
                continue

            # 2. 提取 prompt 字段
            prompt_content = original_data.get("prompt")

            if prompt_content is None:
                prompt_content = str(original_data)

            answer = ""
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "user", "content": str(prompt_content)}
                    ],
                    temperature=0.7
                )
                answer = response.choices[0].message.content

            except Exception as e:
                # 记录错误但不中断
                error_msg = f"[ERROR] {str(e)}"
                print(f"\nRequest failed: {error_msg}")
                answer = error_msg
                time.sleep(2)  # 出错时稍微多等一会

            # 4. 构造输出记录
            record = {
                "model": MODEL_NAME,
                "original_data": original_data,
                "used_prompt": prompt_content,
                "response": answer
            }

            fout.write(json.dumps(record, ensure_ascii=False) + "\n")

            # === [核心修改] 强制刷新缓冲区 ===
            # 确保每写一行就存入硬盘，防止程序意外停止导致数据丢失
            fout.flush()

            pbar.update(1)

            time.sleep(0.2)

    print(f"[DONE] Inference finished. Results saved to: {output_file}")


# ======================
# 6. 运行入口
# ======================

if __name__ == "__main__":
    run_inference(INPUT_FILE, OUTPUT_FILE)