import os  # 整理:环境变量读取key
import json
import hashlib
import sys
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm
import tiktoken
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, Event

# ======================
# 1. API 与 目录配置
# ======================

API_KEY = os.environ.get("DYBENCH_API_KEY", "")
BASE_URL = "https://api.whatai.cc/v1"

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

EMBEDDING_MODEL = "qwen3-embedding-8b"
MAX_TOKENS = 30000

# 并发数设置
CONCURRENCY_LEVEL = 50

# 将这里替换为你存放原始 jsonl 数据的根目录路径 (即 dybencheval_dataset_in_progress 的路径)
INPUT_DIRECTORY = Path("./data/dybencheval_dataset/dybencheval_dataset_in_progress")
# 输出文件路径（所有数据将合并保存到这一个文件中）
OUTPUT_FILE = Path("./external/embeddings/all_datasets_embedded_new.jsonl")

# 全局中止信号（当API报错时触发）
ABORT_EVENT = Event()

# ======================
# 2. Tokenizer
# ======================

tokenizer = tiktoken.get_encoding("cl100k_base")


# ======================
# 3. 辅助函数
# ======================

def truncate_by_tokens(text: str, max_tokens: int = MAX_TOKENS) -> str:
    if not text:
        return " "

    tokens = tokenizer.encode(str(text))
    if len(tokens) <= max_tokens:
        return text
    return tokenizer.decode(tokens[:max_tokens])


def generate_id(domain: str, task: str, text: str) -> str:
    """生成唯一的 MD5 哈希值作为 ID，也可用于识别某条数据是否已经处理过"""
    return hashlib.md5((str(domain) + str(task) + str(text)).encode("utf-8")).hexdigest()


# ======================
# 4. 单行处理逻辑 (供线程池调用)
# ======================

def process_single_item(item: dict, fout, write_lock: Lock):
    """处理单条数据的完整逻辑"""

    if ABORT_EVENT.is_set():
        return False

    text = item["text"]
    if not text.strip():
        return False

    safe_text = truncate_by_tokens(text)

    try:
        # 发起 Embedding 请求 (单条文本)
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[safe_text]
        )

        text_embedding = response.data[0].embedding

        # 按照需求组装输出格式
        out_sample = {
            "id": item["id"],
            "task": item["task"],
            "domain": item["domain"],
            "text": text,
            "text_embedding": text_embedding
        }

        result_str = json.dumps(out_sample, ensure_ascii=False) + "\n"

        # 使用线程锁保护全局文件写入
        with write_lock:
            fout.write(result_str)

        return True

    except Exception as e:
        print(f"\n[Fatal Error] API 请求失败，位于文件 {item['file_name']}。错误信息: {e}")
        ABORT_EVENT.set()  # 触发终止信号
        return False


# ======================
# 5. 主流程
# ======================

def main():
    if not INPUT_DIRECTORY.exists():
        print(f"输入目录不存在: {INPUT_DIRECTORY}")
        return

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 1. 断点续传：读取已处理数据的 ID (Hash)
    processed_ids = set()
    if OUTPUT_FILE.exists():
        print("正在读取已存在的输出文件，加载断点进度...")
        with OUTPUT_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    exist_sample = json.loads(line)
                    if "id" in exist_sample:
                        processed_ids.add(exist_sample["id"])
                except Exception:
                    continue
        if processed_ids:
            print(f"检测到 {len(processed_ids)} 条已处理记录，准备继续执行...")

    # 2. 获取所有的 jsonl 文件 (递归搜索所有子目录)
    # 假设你的输出文件不在该输入目录下，如果在，需要将其过滤掉
    jsonl_files = [f for f in INPUT_DIRECTORY.rglob("*.jsonl")]

    if not jsonl_files:
        print(f"未在 {INPUT_DIRECTORY} 中找到需要处理的 .jsonl 文件。")
        return

    write_lock = Lock()

    # 以追加模式 "a" 打开单一的全局输出文件
    with OUTPUT_FILE.open("a", encoding="utf-8") as fout:

        for file_path in jsonl_files:
            if ABORT_EVENT.is_set():
                break

            # 3. 从目录结构中提取 Domain 和 Task
            # 例如路径: .../Humanity/1_基本NLP任务/billsum_test.jsonl
            task_name = file_path.parent.name  # e.g., 1_基本NLP任务
            domain_name = file_path.parent.parent.name  # e.g., Humanity

            pending_items = []

            # 读取当前文件并过滤已处理过的数据
            with file_path.open("r", encoding="utf-8") as fin:
                for line in fin:
                    if not line.strip(): continue
                    try:
                        sample = json.loads(line)

                        # 尝试获取 text 字段。如果原数据集不是用 'text' 作为键，
                        # 默认将整个 json object 转为字符串进行 embedding
                        text = sample.get("text")
                        if not text:
                            text = json.dumps(sample, ensure_ascii=False)

                        # 生成全局唯一 ID 兼 Hash 校验码
                        item_id = generate_id(domain_name, task_name, text)

                        if item_id not in processed_ids:
                            pending_items.append({
                                "id": item_id,
                                "domain": domain_name,
                                "task": task_name,
                                "text": text,
                                "file_name": file_path.name
                            })
                    except Exception:
                        continue

            if not pending_items:
                print(f"[{file_path.name}] 所有数据均已处理完毕，跳过。")
                continue

            # 4. 开启线程池处理当前文件中的待处理任务
            with ThreadPoolExecutor(max_workers=CONCURRENCY_LEVEL) as executor:
                futures = [
                    executor.submit(process_single_item, item, fout, write_lock)
                    for item in pending_items
                ]

                for future in tqdm(
                        as_completed(futures),
                        total=len(futures),
                        desc=f"Embedding {domain_name}/{task_name}/{file_path.name}",
                        unit="samples",
                        dynamic_ncols=True
                ):
                    if ABORT_EVENT.is_set():
                        print("\n[系统提示] 检测到 API 报错，正在停止所有任务并退出程序...")
                        sys.exit(1)

    if not ABORT_EVENT.is_set():
        print("所有文件均已处理完毕，已合并保存到全局输出文件中！")


if __name__ == "__main__":
    main()
