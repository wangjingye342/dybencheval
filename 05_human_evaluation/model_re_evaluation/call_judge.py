import os  # 整理:环境变量读取key
import json
import time
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm

# ======================
# API 配置
# ======================
API_KEY = os.environ.get("DYBENCH_API_KEY", "")
BASE_URL = "https://api.whatai.cc/v1"
MODEL_NAME = "gemini-3-pro-preview-thinking-*"

# ======================
# 文件路径
# ======================
INPUT_PROMPT_JSONL = "prompts.jsonl"
OUTPUT_RESPONSE_JSONL = "responses.jsonl"

# ======================
# 运行参数
# ======================
SLEEP_SECONDS = 1.0
MAX_RETRY = 3
TIMEOUT = 120

# ======================
# 初始化客户端
# ======================
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    timeout=TIMEOUT,
)


def call_llm(prompt: str) -> str:
    for attempt in range(MAX_RETRY):
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            if attempt == MAX_RETRY - 1:
                raise
            time.sleep(2)


def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def main():
    input_path = Path(INPUT_PROMPT_JSONL)
    output_path = Path(OUTPUT_RESPONSE_JSONL)

    total_lines = count_lines(input_path)

    with input_path.open("r", encoding="utf-8") as fin, \
         output_path.open("w", encoding="utf-8") as fout, \
         tqdm(total=total_lines, desc="API Inference", unit="sample") as pbar:

        for line_idx, line in enumerate(fin):
            pbar.set_postfix(idx=line_idx)

            line = line.strip()
            if not line:
                pbar.update(1)
                continue

            try:
                item = json.loads(line)
                prompt = item["prompt"]
            except Exception as e:
                print(f"[WARN] Line {line_idx} parse failed: {e}")
                pbar.update(1)
                continue

            try:
                response_text = call_llm(prompt)
            except Exception as e:
                print(f"[ERROR] Line {line_idx} API failed: {e}")
                response_text = ""

            output_record = {
                "prompt": prompt,
                "response": response_text,
                "model": MODEL_NAME,
            }

            fout.write(json.dumps(output_record, ensure_ascii=False) + "\n")

            time.sleep(SLEEP_SECONDS)
            pbar.update(1)

    print(f"Done. Results saved to: {output_path}")


if __name__ == "__main__":
    main()
