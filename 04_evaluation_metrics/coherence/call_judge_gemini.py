import os
import json
import concurrent.futures
from openai import OpenAI
from tqdm import tqdm

# ================= 配置区域 =================
# API 配置
API_KEY = os.environ.get("DYBENCH_API_KEY", "")
BASE_URL = "https://api.whatai.cc/v1"
MODEL_NAME = "gemini-3-pro-preview-thinking-*"

# 路径配置
INPUT_DIR = "./external/metrics/2/promptsonly3_gemini"
OUTPUT_DIR = "./external/metrics/2/response_gemini"

# 并发配置
MAX_WORKERS = 20
# ===========================================

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)


def get_processed_ids(output_path):
    """
    读取输出文件，获取所有已经处理过的 ID 集合。
    用于断点续传。
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
                    # 假设输出中一定包含 'id' 字段
                    if "id" in data:
                        processed_ids.add(data["id"])
                except json.JSONDecodeError:
                    continue  # 跳过损坏的行
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
            except Exception as api_err:
                eval_response = f"[ERROR_During_Generation]: {str(api_err)}"

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
    except Exception as e:
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
        file_name_only, file_extension = os.path.splitext(filename)
        new_filename = f"{file_name_only}_response{file_extension}"
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
                    # 预解析一下只为了拿ID，不做其他操作
                    # 这样比直接传行进去更安全，确保只跑没跑过的ID
                    temp_data = json.loads(line)
                    current_id = temp_data.get("id")

                    # 核心判断：如果ID已经在输出文件中，则跳过
                    if current_id in processed_ids:
                        skipped_count += 1
                    else:
                        lines_to_process.append(line)
                except json.JSONDecodeError:
                    # 如果源文件这行坏了，也许应该跳过或尝试处理，这里选择加入处理队列让 process_single_line 去报错
                    lines_to_process.append(line)

        total_tasks = len(lines_to_process)
        print(f"原始总数: {skipped_count + total_tasks} | 已跳过: {skipped_count} | 剩余待处理: {total_tasks}")

        if total_tasks == 0:
            print("该文件已全部处理完成，跳过。")
            continue

        # --- 步骤 C: 处理剩余任务 (使用追加模式 'a') ---
        # 注意：这里使用 'a' (append) 模式，而不是 'w'
        with open(output_path, 'a', encoding='utf-8') as outfile:

            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                # 提交任务
                future_to_line = {executor.submit(process_single_line, line): line for line in lines_to_process}

                # 使用 tqdm 显示进度
                for future in tqdm(concurrent.futures.as_completed(future_to_line), total=total_tasks,
                                   desc="Processing", unit="lines"):
                    result_str = future.result()

                    if result_str:
                        outfile.write(result_str + "\n")
                        outfile.flush()  # 实时刷新

    print(f"\n所有任务处理完成！结果已保存在: {OUTPUT_DIR}")


if __name__ == "__main__":
    process_datasets()