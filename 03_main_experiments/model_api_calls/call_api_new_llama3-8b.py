import os  # 整理:环境变量读取key
import json
import time
import re
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# ======================
# 1. 配置区域
# ======================

API_KEY = os.environ.get("DYBENCH_API_KEY", "")
BASE_URL = "https://api.26351.com/v1"

MODEL_NAME = "llama-3.1-70b"

INPUT_FILE = "./external/model_runs/constructed_prompts_FINAL.jsonl"
OUTPUT_FILE = Path(
    f"./external/model_runs/all_results/ALL_api_results_llama-31-70b.jsonl"
)

# 新增：并发线程数 (根据 API 限制调整，通常 5-20 比较合适)
MAX_WORKERS = 10

# ======================
# 2. 初始化客户端
# ======================
# OpenAI 客户端是线程安全的，可以在全局初始化后传入线程
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)


# ======================
# 3. 单条数据处理逻辑
# ======================

def process_single_line(line):
    """
    处理单行数据：解析 -> 请求 API -> 返回结果字典
    注意：此函数在子线程中运行
    """
    line = line.strip()
    if not line:
        return None

    try:
        # 1. 解析原始数据
        original_data = json.loads(line)

        # 2. 提取 prompt
        prompt_content = original_data.get("prompt")
        if prompt_content is None:
            prompt_content = str(original_data)

        # 3. 请求 API
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "user", "content": str(prompt_content)}
                ],
                temperature=0.7,
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"[ERROR] {str(e)}"

        # 4. 返回结构化结果
        return {
            "model": MODEL_NAME,
            "original_data": original_data,
            "used_prompt": prompt_content,
            "response": answer
        }

    except json.JSONDecodeError:
        return None
    except Exception as e:
        # 兜底捕获其他不可预知的错误
        return {
            "model": MODEL_NAME,
            "error_global": str(e),
            "raw_line": line
        }


# ======================
# 4. 主推理逻辑（并发版）
# ======================

def run_inference(input_file: str, output_file: Path):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 读取所有行到内存（如果文件非常大达到GB级别，建议改用流式读取）
    print(f"Reading input file: {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]

    total_lines = len(lines)
    print(f"Total lines to process: {total_lines}")

    count = 0

    # 打开输出文件准备写入
    with open(output_file, "w", encoding="utf-8") as fout:

        # 创建线程池
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 提交所有任务
            # future_to_line 用于追踪每个任务（如果需要调试特定行）
            futures = [executor.submit(process_single_line, line) for line in lines]

            # 使用 tqdm 显示进度，as_completed 会在任务完成时立刻 yield
            pbar = tqdm(total=total_lines, desc=f"Concurrent Inference (Threads={MAX_WORKERS})", unit="sample")

            for future in as_completed(futures):
                result = future.result()

                # 如果返回 None (空行或解析失败) 则跳过
                if result:
                    fout.write(json.dumps(result, ensure_ascii=False) + "\n")
                    # 实时刷新缓冲区，防止程序中断数据丢失
                    fout.flush()
                    count += 1

                pbar.update(1)

            pbar.close()

    print(f"\n[DONE] Total completed requests: {count}")
    print(f"[DONE] Results saved to: {output_file}")


# ======================
# 5. 运行入口
# ======================

if __name__ == "__main__":
    # 记录开始时间
    start_time = time.time()

    run_inference(INPUT_FILE, OUTPUT_FILE)

    end_time = time.time()
    print(f"Time elapsed: {end_time - start_time:.2f} seconds")