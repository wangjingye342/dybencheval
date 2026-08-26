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

# [安全建议] 请避免直接在代码中硬编码 API Key，建议使用环境变量
# 这里保留您的结构，但请确保换回您的真实 Key
API_KEY = os.environ.get("DYBENCH_API_KEY", "")  # 请确保这里是有效的 Key

BASE_URL = "https://api.deepseek.com"

MODEL_NAME = "deepseek-reasoner"

INPUT_FILE = "D:/STUDY/2026-project1/project1/main_work/通用模型实验/constructed_prompts_临时增补.jsonl"


# ======================
# 2. 输出文件名构造
# ======================

def sanitize_model_name(name: str) -> str:
    return re.sub(r"[^\w\-]+", "_", name)


model_tag = sanitize_model_name(MODEL_NAME)

OUTPUT_FILE = Path(
    f"D:/STUDY/2026-project1/project1/main_work/通用模型实验/results/api_results_{model_tag}.jsonl"
)

# ======================
# 3. 初始化客户端
# ======================

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)


# ======================
# 4. 辅助函数：统计已处理行数
# ======================
def count_lines(filepath: Path) -> int:
    """统计文件行数，用于确定断点位置"""
    if not filepath.exists():
        return 0
    # 简单的行数统计
    with open(filepath, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


# ======================
# 5. 主推理逻辑（带断点续传）
# ======================

def run_inference(input_file: str, output_file: Path):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print("正在统计输入文件总任务数...")
    # 预统计总行数（只统计非空行，保持与下面遍历逻辑一致）
    with open(input_file, "r", encoding="utf-8") as f:
        total_lines = sum(1 for line in f if line.strip())

    # === [修改点 1] 获取断点位置 ===
    processed_count = count_lines(output_file)

    print(f"总任务数: {total_lines}")
    print(f"已完成数: {processed_count}")

    if processed_count >= total_lines:
        print("所有任务已完成，无需运行。")
        return

    # === [修改点 2] 使用 'a' 模式打开输出文件 (Append) ===
    with open(input_file, "r", encoding="utf-8") as fin, \
            open(output_file, "a", encoding="utf-8") as fout, \
            tqdm(total=total_lines, initial=processed_count, desc="Inference Progress", unit="sample") as pbar:

        # 这里的 index 用于记录输入文件读到了第几个有效行
        current_idx = 0

        for line in fin:
            line = line.strip()
            if not line:
                continue

            # 这是一个有效行，计数器+1
            current_idx += 1

            # === [修改点 3] 跳过已处理的数据 ===
            # 如果当前行的序号 <= 已处理行数，说明之前跑过了，直接跳过
            if current_idx <= processed_count:
                continue

            # --- 以下是正常的推理逻辑 ---

            try:
                original_data = json.loads(line)
            except json.JSONDecodeError:
                print(f"[WARN] Line {current_idx} JSON decode error, skipping.")
                continue

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
                # 遇到错误记录错误信息，不中断程序
                error_msg = f"[ERROR] {str(e)}"
                print(f"\nRequest failed: {error_msg}")
                answer = error_msg
                time.sleep(2)  # 出错时多等待一会儿

            record = {
                "model": MODEL_NAME,
                "original_data": original_data,
                "used_prompt": prompt_content,
                "response": answer
            }

            fout.write(json.dumps(record, ensure_ascii=False) + "\n")

            # === [修改点 4] 强制刷新缓冲区 ===
            # 确保即使程序崩溃，刚写入的这一行也会保存到磁盘
            fout.flush()

            pbar.update(1)

            # DeepSeek 对 QPS 较敏感，建议保留 sleep
            time.sleep(0.2)

    print(f"[DONE] Total completed requests: {current_idx}")
    print(f"[DONE] Results saved to: {output_file}")


# ======================
# 6. 运行入口
# ======================

if __name__ == "__main__":
    run_inference(INPUT_FILE, OUTPUT_FILE)