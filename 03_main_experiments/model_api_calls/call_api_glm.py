import json
import time
import re
import os
from pathlib import Path
from tqdm import tqdm
from zhipuai import ZhipuAI

# ======================
# 1. 配置区域
# ======================

# [安全提示] 建议将 Key 放入环境变量。
# 请在此处填入您真实的 API Key
API_KEY = os.environ.get("DYBENCH_API_KEY", "")

# 智谱 GLM-4.6 模型名 (请确认模型名称是否正确，标准名称通常为 glm-4, glm-4-plus 等)
MODEL_NAME = "GLM-4.6"

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
# 3. 初始化智谱客户端
# ======================

client = ZhipuAI(api_key=API_KEY)


# ======================
# 4. 辅助函数：计算已处理行数
# ======================

def count_lines(filepath: Path) -> int:
    """计算文件已有行数，作为断点位置"""
    if not filepath.exists():
        return 0
    with open(filepath, "r", encoding="utf-8") as f:
        # 统计文件中的行数
        return sum(1 for _ in f)


# ======================
# 5. 主推理逻辑（带断点续传）
# ======================

def run_inference(input_file: str, output_file: Path):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print("正在统计输入文件总任务数...")
    # 预统计总行数（只统计非空行，保持计数逻辑一致）
    with open(input_file, "r", encoding="utf-8") as f:
        total_input_lines = sum(1 for line in f if line.strip())

    # === [修改点 1] 获取断点位置 ===
    processed_count = count_lines(output_file)

    print(f"总任务数: {total_input_lines}")
    print(f"已完成数: {processed_count}")

    if processed_count >= total_input_lines:
        print("所有任务已完成，无需运行。")
        return

    # === [修改点 2] 使用 'a' (append) 模式打开输出文件 ===
    with open(input_file, "r", encoding="utf-8") as fin, \
            open(output_file, "a", encoding="utf-8") as fout, \
            tqdm(total=total_input_lines, initial=processed_count, desc="Inference Progress", unit="sample") as pbar:

        # 用于记录当前读取到了输入文件的第几个有效行
        valid_line_idx = 0

        for line in fin:
            line = line.strip()
            if not line:
                continue

            # 这是一个有效行，计数器+1
            valid_line_idx += 1

            # === [修改点 3] 核心跳过逻辑 ===
            # 如果当前行的序号 <= 已处理的行数，说明之前跑过了，直接跳过
            if valid_line_idx <= processed_count:
                continue

            # --- 以下是正常的推理逻辑 ---

            # 1. 解析原始数据
            try:
                original_data = json.loads(line)
            except json.JSONDecodeError:
                print(f"[WARN] JSON decode error at line {valid_line_idx}, skipping.")
                continue

            # 2. 提取 prompt
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
                # 遇到错误记录下来，不要崩溃
                error_msg = f"[ERROR] {str(e)}"
                print(f"\nRequest failed at line {valid_line_idx}: {error_msg}")
                answer = error_msg
                time.sleep(2)  # 出错后多等待一下

            # 3. 构造输出记录
            record = {
                "model": MODEL_NAME,
                "original_data": original_data,
                "used_prompt": prompt_content,
                "response": answer
            }

            fout.write(json.dumps(record, ensure_ascii=False) + "\n")

            # === [修改点 4] 立即刷新缓冲区 ===
            # 确保每写一行就存入硬盘，防止程序崩溃导致最后一条数据丢失
            fout.flush()

            pbar.update(1)

            # 控制请求频率
            time.sleep(0.2)

    print(f"[DONE] Inference finished. Results saved to: {output_file}")


# ======================
# 6. 运行入口
# ======================

if __name__ == "__main__":
    run_inference(INPUT_FILE, OUTPUT_FILE)