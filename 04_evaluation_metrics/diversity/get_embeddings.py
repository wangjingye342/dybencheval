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
MAX_TOKENS = 32000

# 并发数设置
CONCURRENCY_LEVEL = 50

# 将这里替换为你存放原始 jsonl 数据的目录路径
INPUT_DIRECTORY = Path("./external/metrics/1/similarity")
# 输出目录
OUTPUT_DIRECTORY = Path("./external/metrics/1/re_embedding")

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


def generate_hash(seed: str, response: str) -> str:
    """生成唯一的 MD5 哈希值，用于识别某条数据是否已经处理过"""
    return hashlib.md5((str(seed) + str(response)).encode("utf-8")).hexdigest()


# ======================
# 4. 单行处理逻辑 (供线程池调用)
# ======================

def process_single_line(line: str, fout, write_lock: Lock, filename: str):
    """处理单条数据的完整逻辑"""

    # ===== 核心修改点 2：检查全局中断信号 =====
    # 如果其他线程已经触发了报错中断，当前线程直接退出，不再发请求
    if ABORT_EVENT.is_set():
        return False

    if not line.strip():
        return False

    sample = json.loads(line)

    seed_text = sample.get("seed_text", "")
    response_text = sample.get("response_text", "")

    safe_seed = truncate_by_tokens(seed_text)
    safe_response = truncate_by_tokens(response_text)

    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[safe_seed, safe_response]
        )

        seed_embedding = response.data[0].embedding
        response_embedding = response.data[1].embedding

        sample["seed_text_embedding"] = seed_embedding
        sample["response_text_embedding"] = response_embedding

        result_str = json.dumps(sample, ensure_ascii=False) + "\n"

        # 使用线程锁保护文件写入
        with write_lock:
            fout.write(result_str)

        return True

    except Exception as e:
        # ===== 核心修改点 2：API 报错时，触发全局中断信号 =====
        print(f"\n[Fatal Error] API 请求失败，位于文件 {filename}。错误信息: {e}")
        ABORT_EVENT.set()  # 触发终止信号
        return False


# ======================
# 5. Embedding 主逻辑
# ======================

def embed_dataset(input_path: Path, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ===== 核心修改点 1：断点续传（获取已处理数据的哈希记录） =====
    processed_hashes = set()
    if output_path.exists():
        with output_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    exist_sample = json.loads(line)
                    seed = exist_sample.get("seed_text", "")
                    resp = exist_sample.get("response_text", "")
                    processed_hashes.add(generate_hash(seed, resp))
                except Exception:
                    continue
        if processed_hashes:
            print(
                f"[{input_path.name}] 检测到已存在的输出文件，发现 {len(processed_hashes)} 条已处理记录，准备继续执行...")

    # 读取输入文件并过滤掉已经处理过的行
    pending_lines = []
    with input_path.open("r", encoding="utf-8") as fin:
        for line in fin:
            if not line.strip(): continue
            try:
                sample = json.loads(line)
                seed = sample.get("seed_text", "")
                resp = sample.get("response_text", "")
                # 如果哈希值不在已处理集合中，则说明是新数据，加入待处理列表
                if generate_hash(seed, resp) not in processed_hashes:
                    pending_lines.append(line)
            except Exception:
                continue

    if not pending_lines:
        print(f"[{input_path.name}] 所有数据均已处理完毕，跳过。")
        return

    write_lock = Lock()

    # ===== 核心修改点 1：使用 "a" (append 追加模式) 代替 "w" =====
    with output_path.open("a", encoding="utf-8") as fout:

        with ThreadPoolExecutor(max_workers=CONCURRENCY_LEVEL) as executor:
            # 提交待处理的任务
            futures = [
                executor.submit(process_single_line, line, fout, write_lock, input_path.name)
                for line in pending_lines
            ]

            for future in tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc=f"Embedding {input_path.name}",
                    unit="samples",
                    dynamic_ncols=True
            ):
                # ===== 核心修改点 2：主线程监控中断信号 =====
                if ABORT_EVENT.is_set():
                    print("\n[系统提示] 检测到 API 报错，正在停止所有任务并退出程序...")
                    # 直接强制退出 Python 进程
                    sys.exit(1)


# ======================
# 6. 总体流程（自动扫描目录）
# ======================

def main():
    jsonl_files = list(INPUT_DIRECTORY.glob("*.jsonl"))

    # 移除文件过滤逻辑（改为在 embed_dataset 内部进行精细的断点判断）
    # 以免因为只生成了一半的 _embedded.jsonl 被跳过整个文件
    # jsonl_files = [f for f in jsonl_files if not f.name.endswith("_embedded.jsonl")]

    if not jsonl_files:
        print(f"未在 {INPUT_DIRECTORY} 中找到需要处理的 .jsonl 文件。")
        return

    for input_path in jsonl_files:
        # 防止误处理已经生成的 output 文件
        if input_path.name.endswith("_embedded.jsonl"):
            continue

        output_path = OUTPUT_DIRECTORY / f"{input_path.stem}_embedded.jsonl"
        embed_dataset(input_path, output_path)

    if not ABORT_EVENT.is_set():
        print("所有文件处理完毕！")


if __name__ == "__main__":
    main()