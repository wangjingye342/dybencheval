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
BASE_URL = "https://jeniya.cn"

MODEL_NAME = "llama-3-8b"

INPUT_FILE = "D:/STUDY/2026-project1/project1/main_work/通用模型实验/constructed_prompts.jsonl"


# ======================
# 2. 输出文件名构造
# ======================

def sanitize_model_name(name: str) -> str:
    return re.sub(r"[^\w\-]+", "_", name)


model_tag = sanitize_model_name(MODEL_NAME)

OUTPUT_FILE = Path(
    f"D:/STUDY/2026-project1/project1/main_work/通用模型实验/不需要增补_results/small/api_results_{model_tag}.jsonl"
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

            # 1. 解析原始数据行
            original_data = json.loads(line)

            # 2. 提取 prompt 字段 (增加容错，如果找不到prompt字段则报错或跳过)
            # 这里假设数据中必然包含 "prompt" 键
            prompt_content = original_data.get("prompt")

            # 如果提取的内容为空或不是字符串，做个简单的转换确保API不报错
            if prompt_content is None:
                prompt_content = str(original_data)  # 兜底逻辑

            answer = ""
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        # 3. 这里只传入提取出的 prompt 文本，而不是整个 dict
                        {"role": "user", "content": str(prompt_content)}
                    ],
                    temperature=0.7
                )
                answer = response.choices[0].message.content

            except Exception as e:
                answer = f"[ERROR] {str(e)}"

            # 4. 构造输出记录
            # 建议保留原始数据(original_data)，以便后续知道这个答案对应哪个问题
            record = {
                "model": MODEL_NAME,
                "original_data": original_data,  # 保存原始完整数据
                "used_prompt": prompt_content,  # 记录实际喂给API的问题
                "response": answer
            }

            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
            pbar.update(1)

            time.sleep(0.2)

    print(f"[DONE] Total completed requests: {count}")
    print(f"[DONE] Results saved to: {output_file}")


# ======================
# 5. 运行入口
# ======================

if __name__ == "__main__":
    run_inference(INPUT_FILE, OUTPUT_FILE)