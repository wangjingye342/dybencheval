import json
import hashlib
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# ======================
# 1. 目录与文件配置
# ======================

# 包含已知 Embedding 的参考文件
REFERENCE_FILE = Path(
    r".\external\metrics\embeddings\claude_seed_response_extracted_embedded.jsonl")

# 存放原始 jsonl 数据的根目录路径 (dybencheval_dataset_in_progress)
INPUT_DIRECTORY = Path(r"./data/dybencheval_dataset/dybencheval_dataset_in_progress")

# 输出文件路径（合并后的最终文件）
OUTPUT_FILE = Path(r".\external\embeddings\all_datasets_embedded_local.jsonl")

# 并发数设置 (本地查字典速度极快，并发主要用于加速文件 IO 构建)
CONCURRENCY_LEVEL = 50


# ======================
# 2. 辅助函数
# ======================

def generate_id(domain: str, task: str, text: str) -> str:
    """生成唯一的 MD5 哈希值作为 ID，用于断点续传去重"""
    return hashlib.md5((str(domain) + str(task) + str(text)).encode("utf-8")).hexdigest()


def load_reference_embeddings(filepath: Path) -> dict:
    """将参考文件加载到内存字典中，以 seed_text 为 key，embedding 为 value"""
    print(f"正在加载参考 Embedding 数据: {filepath.name} ...")
    ref_dict = {}
    if not filepath.exists():
        print(f"[错误] 找不到参考文件: {filepath}")
        return ref_dict

    with filepath.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try:
                data = json.loads(line)
                seed = data.get("seed_text")
                embedding = data.get("seed_text_embedding")

                # 只有当 seed_text 和 embedding 都存在时才加入字典
                if seed and embedding:
                    ref_dict[seed] = embedding
            except Exception:
                continue

    print(f"加载完成！共读取 {len(ref_dict)} 条参考 Embedding 数据。\n")
    return ref_dict


# ======================
# 3. 单行处理逻辑 (供线程池调用)
# ======================

def process_single_item(item: dict, ref_dict: dict, fout, write_lock: Lock) -> bool:
    """处理单条数据的完整逻辑 (本地匹配版)"""

    text = item["text"]
    if not text.strip():
        return False

    # 核心修改：从本地字典中检索 Embedding
    # 注意：这里要求目标文件的 text 与参考文件的 seed_text 必须完全一致（Exact Match）
    text_embedding = ref_dict.get(text)

    if not text_embedding:
        # 如果在参考文件中找不到对应的 seed_text，则跳过该条数据
        return False

    try:
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
        print(f"\n[Error] 写入数据时发生错误: {e}")
        return False


# ======================
# 4. 主流程
# ======================

def main():
    if not INPUT_DIRECTORY.exists():
        print(f"输入目录不存在: {INPUT_DIRECTORY}")
        return

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 1. 预加载参考 Embedding 字典
    reference_embeddings = load_reference_embeddings(REFERENCE_FILE)
    if not reference_embeddings:
        return

    # 2. 断点续传：读取已处理数据的 ID (Hash)
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
            print(f"检测到 {len(processed_ids)} 条已处理记录，准备继续执行...\n")

    # 3. 获取所有的 jsonl 文件 (递归搜索所有子目录)
    jsonl_files = [f for f in INPUT_DIRECTORY.rglob("*.jsonl")]

    if not jsonl_files:
        print(f"未在 {INPUT_DIRECTORY} 中找到需要处理的 .jsonl 文件。")
        return

    write_lock = Lock()
    total_matched = 0
    total_missing = 0

    # 以追加模式 "a" 打开单一的全局输出文件
    with OUTPUT_FILE.open("a", encoding="utf-8") as fout:

        for file_path in jsonl_files:
            # 从目录结构中提取 Domain 和 Task
            task_name = file_path.parent.name  # e.g., 1_基本NLP任务
            domain_name = file_path.parent.parent.name  # e.g., Humanity

            pending_items = []

            # 读取当前文件并过滤已处理过的数据
            with file_path.open("r", encoding="utf-8") as fin:
                for line in fin:
                    if not line.strip(): continue
                    try:
                        sample = json.loads(line)

                        # 获取要用来匹配的文本内容
                        # 如果你的原始数据集中的键名不叫 "text"，请在这里修改
                        text = sample.get("text", "")

                        # 生成全局唯一 ID 兼 Hash 校验码
                        item_id = generate_id(domain_name, task_name, text)

                        if item_id not in processed_ids:
                            pending_items.append({
                                "id": item_id,
                                "domain": domain_name,
                                "task": task_name,
                                "text": text
                            })
                    except Exception:
                        continue

            if not pending_items:
                print(f"[{file_path.name}] 所有数据均已处理或跳过。")
                continue

            # 4. 开启线程池处理当前文件中的待处理任务
            matched_in_file = 0
            with ThreadPoolExecutor(max_workers=CONCURRENCY_LEVEL) as executor:
                futures = [
                    executor.submit(process_single_item, item, reference_embeddings, fout, write_lock)
                    for item in pending_items
                ]

                for future in tqdm(
                        as_completed(futures),
                        total=len(futures),
                        desc=f"处理 {domain_name}/{task_name}/{file_path.name}",
                        unit="条",
                        dynamic_ncols=True
                ):
                    # 如果返回 True 代表匹配成功并写入
                    if future.result():
                        matched_in_file += 1

            missing_in_file = len(pending_items) - matched_in_file
            total_matched += matched_in_file
            total_missing += missing_in_file

            if missing_in_file > 0:
                print(f"  -> [提示] 该文件中有 {missing_in_file} 条数据在参考字典中未找到匹配项。")

    print("\n==============================")
    print("所有文件均已处理完毕！")
    print(f"成功匹配并保存: {total_matched} 条")
    print(f"未找到匹配项跳过: {total_missing} 条")
    print(f"输出文件路径: {OUTPUT_FILE}")
    print("==============================")


if __name__ == "__main__":
    main()
