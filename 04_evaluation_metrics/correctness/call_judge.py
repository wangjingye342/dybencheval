import os
import json
import time
import random  # [新增] 用于重试时的随机等待
import concurrent.futures
from openai import OpenAI, APIConnectionError, RateLimitError, APITimeoutError  # [新增] 引入具体的异常类型
from tqdm import tqdm

# ================= 配置区域 =================
# API 配置
API_KEY = os.environ.get("DYBENCH_API_KEY", "")
BASE_URL = "https://api.whatai.cc/v1"
MODEL_NAME = "gemini-3-pro-preview-thinking-*"

# 路径配置
INPUT_DIR = "prompts-gemini"
OUTPUT_DIR = "response-gemini"

# 并发配置
# [建议] 如果还是频繁报错，尝试将此处改小，例如 5 或 10
MAX_WORKERS = 20

# 重试配置 [新增]
MAX_RETRIES = 5  # 遇到连接错误最多重试 5 次
RETRY_DELAY = 3  # 初始等待 3 秒
# ===========================================

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

def get_processed_ids(output_path):
    """
    读取输出文件，获取所有已经处理过的 ID 集合。
    """
    processed_ids = set()
    if not os.path.exists(output_path):
        return processed_ids

    print(f"检测到输出文件 {output_path} 已存在，正在扫描已完成的 ID...")
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if "id" in data:
                        processed_ids.add(data["id"])
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"读取已处理文件时出错: {e}")

    print(f"-> 已找到 {len(processed_ids)} 个已处理的任务。")
    return processed_ids


def process_single_line(line):
    """
    处理单行数据的函数 (包含重试机制)
    """
    line = line.strip()
    if not line:
        return None

    try:
        data = json.loads(line)
        prompt_content = data.get("prompt", "")
        eval_response = ""

        if not prompt_content:
            eval_response = ""
        else:
            # [修改关键点] 增加重试循环
            # 我们在这里尝试多次，如果只是网络抖动，就能自动恢复，不会导致主程序崩溃
            for attempt in range(MAX_RETRIES):
                try:
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[
                            {"role": "user", "content": prompt_content}
                        ],
                        temperature=0.7,
                        max_tokens=8196
                    )
                    eval_response = response.choices[0].message.content
                    break  # 如果成功，跳出重试循环

                except (APIConnectionError, APITimeoutError, RateLimitError) as e:
                    # 如果是连接错误、超时或限流，我们进行等待并重试
                    if attempt < MAX_RETRIES - 1:
                        # 指数退避 + 随机抖动 (避免所有线程同时重试)
                        sleep_time = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                        # 这里可以打印一下，或者选择默默重试
                        # print(f"网络波动 (尝试 {attempt+1}/{MAX_RETRIES})，等待 {sleep_time:.1f}秒...")
                        time.sleep(sleep_time)
                    else:
                        # 如果达到最大重试次数，依然失败，则抛出异常，让主线程停止
                        raise e
                except Exception as e:
                    # 其他未知错误（如参数错误），不重试，直接抛出
                    raise e

        output_data = {
            "id": data.get("id"),
            "model": data.get("model"),
            "seed_text": data.get("seed_text"),
            "response_text": data.get("response_text"),
            "eval_response": eval_response
        }
        return json.dumps(output_data, ensure_ascii=False)

    except json.JSONDecodeError:
        return None
    # 注意：如果重试多次后依然失败，这里会抛出异常，被主线程捕获并停止程序


def process_datasets():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"已创建输出目录: {OUTPUT_DIR}")

    try:
        files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.jsonl')]
    except FileNotFoundError:
        print(f"错误: 找不到输入目录 {INPUT_DIR}")
        return

    if not files:
        print(f"在 {INPUT_DIR} 下未找到 .jsonl 文件。")
        return

    files.sort()
    total_files = len(files)
    print(f"共发现 {total_files} 个数据集文件，使用 {MAX_WORKERS} 个线程开始处理...")

    for index, filename in enumerate(files):
        input_path = os.path.join(INPUT_DIR, filename)
        file_name_only, file_extension = os.path.splitext(filename)
        new_filename = f"{file_name_only}_response{file_extension}"
        output_path = os.path.join(OUTPUT_DIR, new_filename)

        print(f"\n{'=' * 50}")
        print(f"正在处理文件 ({index + 1}/{total_files}): {filename}")
        print(f"输出路径: {output_path}")

        processed_ids = get_processed_ids(output_path)

        lines_to_process = []
        skipped_count = 0

        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    temp_data = json.loads(line)
                    if temp_data.get("id") in processed_ids:
                        skipped_count += 1
                    else:
                        lines_to_process.append(line)
                except json.JSONDecodeError:
                    lines_to_process.append(line)

        total_tasks = len(lines_to_process)
        print(f"原始总数: {skipped_count + total_tasks} | 已跳过: {skipped_count} | 剩余待处理: {total_tasks}")

        if total_tasks == 0:
            print("该文件已全部处理完成，跳过。")
            continue

        stop_execution = False

        with open(output_path, 'a', encoding='utf-8') as outfile:
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_line = {executor.submit(process_single_line, line): line for line in lines_to_process}

                progress_bar = tqdm(concurrent.futures.as_completed(future_to_line), total=total_tasks,
                                    desc="Processing", unit="lines")

                for future in progress_bar:
                    try:
                        result_str = future.result()
                        if result_str:
                            outfile.write(result_str + "\n")
                            outfile.flush()
                    except Exception as e:
                        # 只有当重试了 MAX_RETRIES 次依然失败，才会走到这里
                        print(f"\n\n!!!!!! 发生严重错误，停止运行 !!!!!!")
                        print(f"错误详情: {e}")
                        executor.shutdown(wait=False, cancel_futures=True)
                        stop_execution = True
                        break

                progress_bar.close()

        if stop_execution:
            print("程序因错误已终止。")
            return

        if index < total_files - 1:
            print(f"\n文件 {filename} 处理完成。")
            print("正在休息 2 分钟，准备处理下一个数据集...")
            time.sleep(120)
            print("休息结束，继续工作。")

    print(f"\n所有任务处理完成！结果已保存在: {OUTPUT_DIR}")


if __name__ == "__main__":
    process_datasets()