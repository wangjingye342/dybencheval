import os
import json
import concurrent.futures
import threading
import sys  # 引入 sys 用于强制退出
from openai import OpenAI
from tqdm import tqdm

# ================= 配置区域 =================
# API 配置
API_KEY = os.environ.get("DYBENCH_API_KEY", "")
BASE_URL = "https://api.whatai.cc/v1"
# MODEL_NAME = "claude-opus-4-6-thinking"
# MODEL_NAME = "gemini-3-pro-preview-thinking-*"
MODEL_NAME = "gpt-5.2"

# 路径配置
INPUT_DIR = "D:/STUDY/2026-project1/project1/main_work/计算指标/2/0re/prompt_gpt52/"
OUTPUT_DIR = "D:/STUDY/2026-project1/project1/main_work/计算指标/2/0re/response_gpt_re_ori"

# 并发配置
MAX_WORKERS = 20
# ===========================================

# 全局停止信号
STOP_EVENT = threading.Event()

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
    # 1. 检查是否触发了停止信号，如果触发直接返回 None，不再请求 API
    if STOP_EVENT.is_set():
        return None

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
                # ================= 报错处理核心修改 =================
                error_msg = str(api_err)
                print(f"\n[!!! CRITICAL ERROR !!!] API 请求失败: {error_msg}")
                print("正在触发全局停止...")

                # 触发全局停止信号
                STOP_EVENT.set()

                # 返回 None，确保这条错误数据不会被写入文件
                return None
                # =================================================

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
        # 如果是代码逻辑错误而非API错误，也打印一下，但不一定非要强制停止
        # 如果希望任何错误都停止，也可以在这里 set()
        return None


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

    print(f"共发现 {len(files)} 个数据集文件，使用 {MAX_WORKERS} 个线程开始处理...")

    for filename in files:
        # 如果在文件循环层级发现停止信号，直接退出
        if STOP_EVENT.is_set():
            break

        input_path = os.path.join(INPUT_DIR, filename)
        file_name_only, file_extension = os.path.splitext(filename)
        new_filename = f"{file_name_only}_response{file_extension}"
        output_path = os.path.join(OUTPUT_DIR, new_filename)

        print(f"\n{'=' * 50}")
        print(f"正在处理文件: {filename}")
        print(f"输出路径: {output_path}")

        processed_ids = get_processed_ids(output_path)

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
                    lines_to_process.append(line)

        total_tasks = len(lines_to_process)
        print(f"原始总数: {skipped_count + total_tasks} | 已跳过: {skipped_count} | 剩余待处理: {total_tasks}")

        if total_tasks == 0:
            print("该文件已全部处理完成，跳过。")
            continue

        with open(output_path, 'a', encoding='utf-8') as outfile:
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_line = {executor.submit(process_single_line, line): line for line in lines_to_process}

                # 使用 tqdm 封装
                pbar = tqdm(concurrent.futures.as_completed(future_to_line), total=total_tasks, desc="Processing",
                            unit="lines")

                for future in pbar:
                    # 每次获取结果前，检查是否需要紧急停止
                    if STOP_EVENT.is_set():
                        pbar.close()
                        print("\n检测到停止信号，正在终止线程池并退出程序...")

                        # 尝试取消剩余任务（Python 3.9+ 支持 cancel_futures=True）
                        # 如果是旧版本 Python，shutdown 后强行 exit 即可
                        executor.shutdown(wait=False)
                        sys.exit(1)  # 强制退出脚本

                    try:
                        result_str = future.result()
                        if result_str:
                            outfile.write(result_str + "\n")
                            outfile.flush()
                    except Exception as e:
                        # 获取 future 结果时发生的意外错误
                        print(f"任务执行异常: {e}")

    if STOP_EVENT.is_set():
        print("\n程序因错误已终止。")
    else:
        print(f"\n所有任务处理完成！结果已保存在: {OUTPUT_DIR}")


if __name__ == "__main__":
    process_datasets()