import os
import json
import time
import random
import concurrent.futures
from openai import OpenAI, APIConnectionError, RateLimitError, APITimeoutError
from tqdm import tqdm

# ================= 配置区域 =================
# API 配置 (请确保 API KEY 有效)
API_KEY = os.environ.get("DYBENCH_API_KEY", "")
BASE_URL = "https://api.whatai.cc/v1"
MODEL_NAME = "gemini-3-pro-preview-thinking-*"  # 建议确认模型名称，gemini-3可能不存在，这里假设是thinking模型，如果你的平台支持gemini-3请改回

# 路径配置
INPUT_DIR = "D:/STUDY/2026-project1/project1/main_work/scripts/后补实验/all_prompts"
OUTPUT_DIR = "D:/STUDY/2026-project1/project1/main_work/scripts/后补实验/all_results"

# 并发配置
MAX_WORKERS = 20  # 根据API限流情况调整，建议10-20

# 重试配置
MAX_RETRIES = 5
RETRY_DELAY = 3
# ===========================================

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)


def get_processed_ids(output_path):
    """
    读取输出文件，获取所有已经处理过的 ID 集合，支持断点续传。
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
                    # 兼容可能存在的不同id字段名，通常是 'id'
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
    处理单行数据的函数
    """
    line = line.strip()
    if not line:
        return None

    try:
        # 1. 解析原始数据
        data = json.loads(line)
        prompt_content = data.get("prompt", "")
        ai_response_content = ""

        # 2. 如果 prompt 为空，跳过请求
        if not prompt_content:
            ai_response_content = ""
        else:
            # 3. 带重试机制的 API 请求
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
                    ai_response_content = response.choices[0].message.content
                    break  # 成功则跳出循环

                except (APIConnectionError, APITimeoutError, RateLimitError) as e:
                    if attempt < MAX_RETRIES - 1:
                        sleep_time = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                        time.sleep(sleep_time)
                    else:
                        raise e  # 最终失败抛出异常
                except Exception as e:
                    raise e  # 其他错误直接抛出

        # 4. 【关键修改】保留原始数据，添加 response 字段
        # 直接在原字典上修改，确保 id, target_task 等所有字段都被保留
        data["response"] = ai_response_content

        return json.dumps(data, ensure_ascii=False)

    except json.JSONDecodeError:
        return None


def process_datasets():
    # 确保输出目录存在
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"已创建输出目录: {OUTPUT_DIR}")

    # 检查输入目录
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

        # 输出文件名保持一致，或者你可以加后缀，这里保持一致以便于对应
        # 如果想加后缀，可以使用: new_filename = f"{os.path.splitext(filename)[0]}_result.jsonl"
        new_filename = f"{os.path.splitext(filename)[0]}_result.jsonl"
        output_path = os.path.join(OUTPUT_DIR, new_filename)

        print(f"\n{'=' * 50}")
        print(f"正在处理文件 ({index + 1}/{total_files}): {new_filename}")
        print(f"输出路径: {output_path}")

        # 获取已处理 ID 实现断点续传
        processed_ids = get_processed_ids(output_path)

        lines_to_process = []
        skipped_count = 0

        # 读取待处理数据
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    temp_data = json.loads(line)
                    # 检查 id 是否已存在于输出文件中
                    if temp_data.get("id") in processed_ids:
                        skipped_count += 1
                    else:
                        lines_to_process.append(line)
                except json.JSONDecodeError:
                    # 如果格式不对，暂且跳过或放入待处理看后续报错
                    pass

        total_tasks = len(lines_to_process)
        print(f"原始总数: {skipped_count + total_tasks} | 已跳过: {skipped_count} | 剩余待处理: {total_tasks}")

        if total_tasks == 0:
            print("该文件已全部处理完成，跳过。")
            continue

        stop_execution = False

        # 追加模式写入 ('a')
        with open(output_path, 'a', encoding='utf-8') as outfile:
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                # 提交任务
                future_to_line = {executor.submit(process_single_line, line): line for line in lines_to_process}

                # 进度条
                progress_bar = tqdm(concurrent.futures.as_completed(future_to_line), total=total_tasks,
                                    desc="Processing", unit="lines")

                for future in progress_bar:
                    try:
                        result_str = future.result()
                        if result_str:
                            outfile.write(result_str + "\n")
                            outfile.flush()  # 确保实时写入磁盘
                    except Exception as e:
                        print(f"\n\n!!!!!! 发生严重错误，停止运行 !!!!!!")
                        print(f"错误详情: {e}")
                        executor.shutdown(wait=False, cancel_futures=True)
                        stop_execution = True
                        break

                progress_bar.close()

        if stop_execution:
            print("程序因错误已终止。请检查网络或 API Key。")
            return

        # 文件间休息策略
        if index < total_files - 1:
            print(f"\n文件 {new_filename} 处理完成。")
            print("正在休息 10 秒，准备处理下一个数据集...")
            time.sleep(10)

    print(f"\n所有任务处理完成！结果已保存在: {OUTPUT_DIR}")


if __name__ == "__main__":
    process_datasets()