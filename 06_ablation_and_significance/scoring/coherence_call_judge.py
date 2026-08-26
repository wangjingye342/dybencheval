import os
import json
import time
import random
import concurrent.futures
from openai import OpenAI, APIConnectionError, RateLimitError, APITimeoutError
from tqdm import tqdm

# ================= 配置区域 =================
# API 配置
API_KEY = os.environ.get("DYBENCH_API_KEY", "")
BASE_URL = "https://api.whatai.cc/v1"
MODEL_NAME = "gemini-3-pro-preview-thinking-*"  # 保持与你提供的一致

# 路径配置
INPUT_DIR = "./external/ablation/evaluation_metrics/2/prompts_coherence"
OUTPUT_DIR = "./external/ablation/evaluation_metrics/2/results_coherence"

# 并发配置
MAX_WORKERS = 20

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
    读取输出文件，获取所有已经处理过的 ID 集合，用于断点续传。
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
    处理单行数据的函数
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
            # 增加重试机制
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
                    break  # 成功则跳出

                except (APIConnectionError, APITimeoutError, RateLimitError) as e:
                    if attempt < MAX_RETRIES - 1:
                        sleep_time = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                        time.sleep(sleep_time)
                    else:
                        eval_response = f"[ERROR_API_FAIL]: {str(e)}"
                except Exception as e:
                    eval_response = f"[ERROR_UNKNOWN]: {str(e)}"
                    break

        # 构造输出数据
        # 注意：这里根据 'Coherence Prompt' 生成时的字段进行了调整
        output_data = {
            "id": data.get("id"),
            "target_task": data.get("target_task"),  # 保留任务标签
            "target_scenario": data.get("target_scenario"),  # 保留情境标签
            "original_response": data.get("original_response"),  # 这是被评测的题目文本
            "eval_response": eval_response  # 这是大模型的评分结果
        }
        return json.dumps(output_data, ensure_ascii=False)

    except json.JSONDecodeError:
        return None


def process_datasets():
    # 1. 确保存储结果的输出目录存在
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

    print(f"共发现 {len(files)} 个数据集文件，使用 {MAX_WORKERS} 个线程开始处理...")

    # 2. 遍历每一个数据集文件
    for filename in files:
        input_path = os.path.join(INPUT_DIR, filename)

        # 构造输出文件名： xxx_prompt_coherence.jsonl -> xxx_result_coherence.jsonl
        # 这样命名更清晰
        file_name_only = filename.replace("_prompt_coherence.jsonl", "")
        if file_name_only == filename:  # 如果没替换成功（后缀不匹配），就直接去后缀
            file_name_only = os.path.splitext(filename)[0]

        new_filename = f"{file_name_only}_result_coherence.jsonl"
        output_path = os.path.join(OUTPUT_DIR, new_filename)

        print(f"\n{'=' * 50}")
        print(f"正在处理文件: {filename}")
        print(f"输出路径: {output_path}")

        # --- 步骤 A: 获取断点信息 ---
        processed_ids = get_processed_ids(output_path)

        # --- 步骤 B: 读取并过滤输入数据 ---
        lines_to_process = []
        skipped_count = 0

        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    temp_data = json.loads(line)
                    current_id = temp_data.get("id")

                    if current_id in processed_ids:
                        skipped_count += 1
                    else:
                        lines_to_process.append(line)
                except json.JSONDecodeError:
                    pass

        total_tasks = len(lines_to_process)
        print(f"原始总数: {skipped_count + total_tasks} | 已跳过: {skipped_count} | 剩余待处理: {total_tasks}")

        if total_tasks == 0:
            print("该文件已全部处理完成，跳过。")
            continue

        # --- 步骤 C: 处理剩余任务 ---
        with open(output_path, 'a', encoding='utf-8') as outfile:
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_line = {executor.submit(process_single_line, line): line for line in lines_to_process}

                for future in tqdm(concurrent.futures.as_completed(future_to_line), total=total_tasks,
                                   desc="Evaluating Coherence", unit="lines"):
                    result_str = future.result()
                    if result_str:
                        outfile.write(result_str + "\n")
                        outfile.flush()

    print(f"\n所有任务处理完成！结果已保存在: {OUTPUT_DIR}")


if __name__ == "__main__":
    process_datasets()