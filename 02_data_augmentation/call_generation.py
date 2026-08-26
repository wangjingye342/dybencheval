import json
import os
import time
from openai import OpenAI
from tqdm import tqdm

# ======================
# 1. 配置区域
# ======================

# API 配置
API_KEY = os.environ.get("DYBENCH_API_KEY", "")
BASE_URL = "https://api.whatai.cc/v1"

# 模型名称
MODEL_NAME = "gemini-3-pro-preview-thinking-*"

# 文件路径配置
INPUT_FILE = "./external/prompts/generated_prompts_SocialScience_Code_Generation.jsonl"
OUTPUT_FILE = "./external/generated_outputs/generated_data_SocialScience_Code_Generation_40.jsonl"

# 初始化客户端
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)


# ======================
# 2. 核心函数
# ======================

def call_llm(prompt, retries=3):
    """调用大模型生成回复，包含重试机制"""
    for i in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # 增加一点随机性以丰富数据
                max_tokens=4096  # 根据需要调整输出长度
            )
            return response.choices[0].message.content
        except Exception as e:
            if i < retries - 1:
                time.sleep(2)  # 等待2秒后重试
                continue
            else:
                print(f"\n[Error] Failed after {retries} retries: {e}")
                return None


def main():
    # 1. 检查输入文件
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file not found: {INPUT_FILE}")
        return

    # 2. 读取已处理的数据量（用于断点续传）
    processed_count = 0
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for _ in f:
                processed_count += 1
        print(f"Found {processed_count} existing results. Resuming...")

    # 3. 读取所有输入数据
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()

    total_lines = len(all_lines)

    # 如果已经全部完成，直接退出
    if processed_count >= total_lines:
        print("All tasks completed. No new prompts to process.")
        return

    # 4. 开始处理
    # 使用 'a' (append) 模式打开输出文件
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f_out:
        # 使用 tqdm 显示进度条，initial 参数用于显示跳过的进度
        for i in tqdm(range(processed_count, total_lines), initial=processed_count, total=total_lines,
                      desc="Generating"):
            line = all_lines[i]
            if not line.strip():
                continue

            try:
                data = json.loads(line)
                prompt_text = data.get("prompt", "")

                if not prompt_text:
                    continue

                # 调用 API
                generated_content = call_llm(prompt_text)

                if generated_content:
                    # 构造结果对象：保留原始Metadata，加入生成结果
                    result_obj = {
                        "target_scenario": data.get("target_scenario"),
                        "target_task": data.get("target_task"),
                        "original_prompt": prompt_text,
                        "generated_response": generated_content,
                        "model_used": MODEL_NAME
                    }

                    # 立即写入文件 (防止程序中断数据丢失)
                    f_out.write(json.dumps(result_obj, ensure_ascii=False) + "\n")
                    f_out.flush()  # 强制刷新缓冲区

            except json.JSONDecodeError:
                print(f"\n[Skip] Invalid JSON format at line {i + 1}")
                continue

    print(f"\nProcessing complete! Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()