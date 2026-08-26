import os  # 整理:环境变量读取key
import json
import time
import re
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm

# ======================
# 1. 配置区域
# ======================

API_KEY = os.environ.get("DYBENCH_API_KEY", "")

BASE_URL = "https://api.deepseek.com"

MODEL_NAME = "deepseek-reasoner"

INPUT_FILE = "./external/model_runs/apiask_sample_5.jsonl"

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
# 4. 主推理逻辑（带进度条）
# ======================

def run_inference(input_file: str, output_file: Path):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 预统计总行数（只统计非空行）
    with open(input_file, "r", encoding="utf-8") as f:
        total_lines = sum(1 for line in f if line.strip())

    count = 0

    with open(input_file, "r", encoding="utf-8") as fin, \
         open(output_file, "w", encoding="utf-8") as fout, \
         tqdm(total=total_lines, desc="Inference Progress", unit="sample") as pbar:

        for line in fin:
            line = line.strip()
            if not line:
                continue

            original_data = json.loads(line)

            prompt_content = original_data.get("prompt")
            if prompt_content is None:
                prompt_content = str(original_data)

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
                answer = f"[ERROR] {str(e)}"

            record = {
                "model": MODEL_NAME,
                "original_data": original_data,
                "used_prompt": prompt_content,
                "response": answer
            }

            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
            pbar.update(1)

            # DeepSeek 对 QPS 较敏感，建议保留 sleep
            time.sleep(0.2)

    print(f"[DONE] Total completed requests: {count}")
    print(f"[DONE] Results saved to: {output_file}")

# ======================
# 5. 运行入口
# ======================

if __name__ == "__main__":
    run_inference(INPUT_FILE, OUTPUT_FILE)
