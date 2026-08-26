import os  # 整理:环境变量读取key
import json
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm
import tiktoken

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

# 将这里替换为你存放原始 jsonl 数据的目录路径
INPUT_DIRECTORY = Path("./external/augmentation_data/input")
# 输出目录（可选：如果你想保存在不同文件夹，可以修改这里。目前默认保存在同级目录）
OUTPUT_DIRECTORY = Path("./external/augmentation_data")

# ======================
# 2. Tokenizer
# ======================

tokenizer = tiktoken.get_encoding("cl100k_base")


# ======================
# 3. Token 截断
# ======================

def truncate_by_tokens(text: str, max_tokens: int = MAX_TOKENS) -> str:
    tokens = tokenizer.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return tokenizer.decode(tokens[:max_tokens])


# ======================
# 4. Embedding 主逻辑
# ======================

def embed_dataset(input_path: Path, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as fin, \
            output_path.open("w", encoding="utf-8") as fout:

        # 统计行数以便 tqdm 显示准确进度
        lines = fin.readlines()

        for line in tqdm(
                lines,
                desc=f"Embedding {input_path.name}",
                unit="samples",
                dynamic_ncols=True
        ):
            if not line.strip():
                continue

            sample = json.loads(line)

            # 注意：这里继续沿用参考代码逻辑，将整条json转换为文本去拿embedding。
            # 如果你只想根据 query 或 question 取 embedding，请修改为 text = sample["question"] 等
            text = json.dumps(sample, ensure_ascii=False)
            text = truncate_by_tokens(text)

            try:
                # 调用 API 获取 embedding
                response = client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=text
                )
                embedding = response.data[0].embedding

                # ===== 核心修改点：直接在原字典中追加 embedding 字段 =====
                sample["embedding"] = embedding

                # 写入更新后的单条数据
                fout.write(json.dumps(sample, ensure_ascii=False) + "\n")

            except Exception as e:
                # 简单的异常处理，防止因为某一条请求报错导致整个文件白跑
                print(f"\n[Error] Failed to embed a sample in {input_path.name}: {e}")
                continue


# ======================
# 5. 总体流程（自动扫描目录）
# ======================

def main():
    # 自动扫描目录下所有的 .jsonl 文件
    jsonl_files = list(INPUT_DIRECTORY.glob("*.jsonl"))

    # 过滤掉已经处理过的文件（防止重复运行）
    jsonl_files = [f for f in jsonl_files if not f.name.endswith("_embedded.jsonl")]

    if not jsonl_files:
        print(f"未在 {INPUT_DIRECTORY} 中找到需要处理的 .jsonl 文件。")
        return

    for input_path in tqdm(
            jsonl_files,
            desc="Processing datasets",
            unit="dataset"
    ):
        # 构造输出文件名：原文件名 + _embedded.jsonl
        output_path = OUTPUT_DIRECTORY / f"{input_path.stem}_embedded.jsonl"
        embed_dataset(input_path, output_path)

    print("所有文件处理完毕！")


if __name__ == "__main__":
    main()