import os  # 整理:环境变量读取key
import json
import time
import re
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from tqdm import tqdm

# ======================
# 1. 配置区域
# ======================

# ⚠️ 请确保填入正确的 API KEY
API_KEY = os.environ.get("DYBENCH_API_KEY", "")
BASE_URL = "https://api.whatai.cc/v1"

MODEL_NAME = "qwen3-8b"
INPUT_FILE = "./external/model_runs/qwen3_8b_sample/qwen3-8b-40条.jsonl"

# 并发数配置
# 建议设置在 5-10 之间，过高可能会触发 API 的速率限制 (429 Too Many Requests)
MAX_WORKERS = 10


# ======================
# 2. 输出文件名构造
# ======================

def sanitize_model_name(name: str) -> str:
    return re.sub(r"[^\w\-]+", "_", name)


model_tag = sanitize_model_name(MODEL_NAME)
OUTPUT_FILE = Path(
    f"./external/model_runs/augmentation_results/api_results_{model_tag}.jsonl"
)

# ======================
# 3. 初始化客户端与全局控制
# ======================

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

# 用于控制紧急停止的事件标志
stop_event = threading.Event()


# ======================
# 4. 单条处理逻辑
# ======================

def process_single_line(line_content):
    """
    处理单行数据的函数，将在线程池中运行
    """
    # 0. 检查是否已经触发了全局停止信号
    if stop_event.is_set():
        return None

    line = line_content.strip()
    if not line:
        return None

    try:
        # 1. 解析数据
        original_data = json.loads(line)
        prompt_content = original_data.get("prompt")
        if prompt_content is None:
            prompt_content = str(original_data)

        # 2. 调用 API
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": str(prompt_content)}
            ],
            temperature=0.7,
            max_tokens=8196,
            # 显式禁用 thinking 以防止报错
            extra_body={"enable_thinking": False},
            # 设置超时时间，防止线程卡死
            timeout=60
        )

        answer = response.choices[0].message.content

        # 3. 返回成功结果
        return {
            "status": "success",
            "record": {
                "model": MODEL_NAME,
                "original_data": original_data,
                "used_prompt": prompt_content,
                "response": answer
            }
        }

    except Exception as e:
        # 捕获任何异常，并触发全局停止
        error_msg = str(e)
        print(f"\n[CRITICAL ERROR] Thread encountered error: {error_msg}")
        print("[ACTION] Triggering emergency stop...")

        # 设置停止信号，通知其他线程和主循环
        stop_event.set()

        return {
            "status": "error",
            "error_msg": error_msg
        }


# ======================
# 5. 主推理逻辑（并发版）
# ======================

def run_inference(input_file: str, output_file: Path):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. 读取所有行到内存（如果文件巨大，几百万行，建议分块读取，但普通jsonl可以直接读）
    print("Reading input file...")
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]

    total_lines = len(lines)
    print(f"Total tasks: {total_lines}, Concurrency: {MAX_WORKERS}")

    completed_count = 0

    # 2. 开启线程池
    with open(output_file, "w", encoding="utf-8") as fout:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 提交所有任务
            # 注意：futures 是乱序完成的
            futures = [executor.submit(process_single_line, line) for line in lines]

            # 使用 tqdm 显示进度，as_completed 会在某个任务完成时立刻 yield
            pbar = tqdm(total=total_lines, desc="Processing", unit="sample")

            for future in as_completed(futures):
                # 检查是否触发了停止信号
                if stop_event.is_set():
                    pbar.write("!!! Process stopped due to API Error !!!")
                    # 取消剩余未开始的任务（Python 3.9+ 支持 cancel_futures=True，这里做兼容处理）
                    executor.shutdown(wait=False)
                    break

                try:
                    result = future.result()

                    # 如果任务被跳过（空行）或因为停止信号返回 None
                    if result is None:
                        continue

                    if result["status"] == "success":
                        # 写入文件
                        fout.write(json.dumps(result["record"], ensure_ascii=False) + "\n")
                        fout.flush()  # 实时落盘
                        completed_count += 1
                        pbar.update(1)

                    elif result["status"] == "error":
                        # 实际上这里的逻辑很少走到，因为 error 会触发 stop_event 并在上方 break
                        # 但为了逻辑完整保留
                        pbar.write(f"Error caught in main loop: {result['error_msg']}")
                        stop_event.set()
                        break

                except Exception as e:
                    pbar.write(f"Unexpected executor error: {e}")
                    stop_event.set()
                    break

            pbar.close()

    if stop_event.is_set():
        print(f"\n[STOPPED] The program was stopped early due to errors.")
        print(f"Check output file for partial results: {output_file}")
    else:
        print(f"\n[DONE] Successfully processed {completed_count} requests.")
        print(f"Results saved to: {output_file}")


# ======================
# 6. 运行入口
# ======================

if __name__ == "__main__":
    run_inference(INPUT_FILE, OUTPUT_FILE)