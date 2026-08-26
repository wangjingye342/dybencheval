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

# 为了安全起见，建议将 Key 放入环境变量或单独的配置文件。
# 在此处运行时请确保填入真实的 Key。
API_KEY = os.environ.get("DYBENCH_API_KEY", "")
BASE_URL = "https://api.whatai.cc/v1"

MODEL_NAME = "claude-opus-4-5-20251101-thinking"

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
    """计算文件行数，用于确定断点位置"""
    if not filepath.exists():
        return 0
    with open(filepath, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


# ======================
# 5. 主推理逻辑（带断点续传）
# ======================

def run_inference(input_file: str, output_file: Path):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. 预统计输入文件总任务数（只统计非空行）
    print("正在统计输入文件总行数...")
    with open(input_file, "r", encoding="utf-8") as f:
        total_input_lines = sum(1 for line in f if line.strip())

    # 2. 检查输出文件，确定已完成的数量 (断点位置)
    processed_count = count_lines(output_file)

    print(f"总任务数: {total_input_lines}")
    print(f"已完成数: {processed_count}")

    if processed_count >= total_input_lines:
        print("所有任务已完成，无需运行。")
        return

    # 3. 打开文件进行处理
    # 注意：输出文件使用 "a" (append) 模式，以保留之前的记录
    with open(input_file, "r", encoding="utf-8") as fin, \
            open(output_file, "a", encoding="utf-8") as fout, \
            tqdm(total=total_input_lines, initial=processed_count, desc="Inference Progress", unit="sample") as pbar:

        valid_input_counter = 0  # 用于记录我们在输入文件中遇到了多少个有效行

        for line in fin:
            line = line.strip()
            if not line:
                continue  # 跳过空行

            # 计数器+1，表示发现了一个有效的输入任务
            valid_input_counter += 1

            # === 断点续传核心逻辑 ===
            # 如果当前发现的有效行数 <= 已处理的行数，说明这一行之前跑过了，跳过
            if valid_input_counter <= processed_count:
                continue

                # === 开始处理新数据 ===

            # 1. 解析原始数据行
            try:
                original_data = json.loads(line)
            except json.JSONDecodeError:
                print(f"[WARN] JSON decode error at line {valid_input_counter}, skipping.")
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
                # 遇到API错误记录下来，不要中断程序
                error_msg = f"[ERROR] {str(e)}"
                print(f"\nRequest failed: {error_msg}")
                answer = error_msg
                # 可选：如果遇到限流 (429)，可以在这里加长一点 sleep
                time.sleep(2)

                # 4. 构造输出记录
            record = {
                "model": MODEL_NAME,
                "original_data": original_data,
                "used_prompt": prompt_content,
                "response": answer
            }

            fout.write(json.dumps(record, ensure_ascii=False) + "\n")

            # === 关键：立即刷新缓冲区 ===
            # 确保每写一行就存入硬盘，防止程序崩溃导致最后几条数据丢失
            fout.flush()

            pbar.update(1)

            # 避免触发并发限制
            time.sleep(0.2)

    print(f"[DONE] Inference finished. Results saved to: {output_file}")


# ======================
# 6. 运行入口
# ======================

if __name__ == "__main__":
    run_inference(INPUT_FILE, OUTPUT_FILE)