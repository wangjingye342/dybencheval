import json
import os
import time
import multiprocessing
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

# --- 全局变量 (用于多进程共享数据) ---
# 在 Linux (AutoDL) 环境下，利用 fork 机制，子进程可以直接读取该变量，无需序列化，效率最高
GLOBAL_TOKENIZED_TEXTS = []
SMOOTH_FN = SmoothingFunction().method1


def worker_calc_bleu(idx):
    """
    多进程的工作函数：计算单个句子的 Self-BLEU
    """
    hyp = GLOBAL_TOKENIZED_TEXTS[idx]
    # 将除了当前句子以外的所有句子作为参考集
    # 注意：这里利用切片，虽然有内存开销，但在多进程中是权衡后的较优解
    refs = GLOBAL_TOKENIZED_TEXTS[:idx] + GLOBAL_TOKENIZED_TEXTS[idx + 1:]

    if not refs:
        return (0, 0, 0, 0)

    # 计算 BLEU 1-4
    try:
        b1 = sentence_bleu(refs, hyp, weights=(1, 0, 0, 0), smoothing_function=SMOOTH_FN)
        b2 = sentence_bleu(refs, hyp, weights=(0.5, 0.5, 0, 0), smoothing_function=SMOOTH_FN)
        b3 = sentence_bleu(refs, hyp, weights=(1 / 3, 1 / 3, 1 / 3, 0), smoothing_function=SMOOTH_FN)
        b4 = sentence_bleu(refs, hyp, weights=(0.25, 0.25, 0.25, 0.25), smoothing_function=SMOOTH_FN)
        return (b1, b2, b3, b4)
    except Exception:
        return (0, 0, 0, 0)


def init_worker(shared_texts):
    """
    初始化工作进程，将数据加载到全局变量
    (主要用于非 Fork 启动方式，虽然 AutoDL 是 Linux，加这个更保险)
    """
    global GLOBAL_TOKENIZED_TEXTS
    GLOBAL_TOKENIZED_TEXTS = shared_texts


def calculate_self_bleu_parallel(file_path):
    """
    并行计算单个文件的 Self-BLEU
    """
    global GLOBAL_TOKENIZED_TEXTS

    # 1. 读取数据
    texts = []
    print(f"正在读取文件: {os.path.basename(file_path)} ...")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    data = json.loads(line)
                    if 'response_text' in data:
                        texts.append(data['response_text'])
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"读取错误: {e}")
        return None

    if len(texts) == 0:
        print(f"数据为空，跳过。")
        return None

    # --- 采样保护 (可选) ---
    # 如果数据量极大（例如超过 5000 条），Self-BLEU 计算量是平方级增长。
    # 为了速度，通常学术界会采样计算。如果不需要采样，请注释掉下面这段。
    # if len(texts) > 5000:
    #     import random
    #     print(f"数据量过大 ({len(texts)}条)，随机采样 2000 条进行计算以加速...")
    #     texts = random.sample(texts, 2000)
    # -----------------------

    # 2. 预处理
    tokenized_texts = [text.lower().split() for text in texts]

    # 更新全局变量供子进程使用
    GLOBAL_TOKENIZED_TEXTS = tokenized_texts

    print(f"[{os.path.basename(file_path)}] 数据量: {len(texts)} 条 | 启动多进程计算...")
    start_time = time.time()

    # 3. 多进程计算
    # 获取 CPU 核心数，保留 1 个核心给系统，防止死机
    cpu_count = max(1, multiprocessing.cpu_count() - 1)

    results = []
    scores_sum = {'bleu1': 0, 'bleu2': 0, 'bleu3': 0, 'bleu4': 0}

    # 使用 Pool 进行并行计算
    # 注意：在 Linux (AutoDL) 上，GLOBAL_TOKENIZED_TEXTS 会通过 fork 自动共享
    with multiprocessing.Pool(processes=cpu_count) as pool:
        # map 会按顺序返回结果
        bleu_scores = pool.map(worker_calc_bleu, range(len(tokenized_texts)))

    # 4. 汇总结果
    for i, (b1, b2, b3, b4) in enumerate(bleu_scores):
        scores_sum['bleu1'] += b1
        scores_sum['bleu2'] += b2
        scores_sum['bleu3'] += b3
        scores_sum['bleu4'] += b4

        # 保存详细结果 (为了减小输出文件体积，通常只保存 avg，若需要详情可取消注释)
        # results.append({
        #     'id': i,
        #     'preview': texts[i][:30],
        #     'bleu4': b4
        # })

    # 计算平均分
    n = len(texts)
    avg_scores = {k: v / n for k, v in scores_sum.items()} if n > 0 else scores_sum

    end_time = time.time()
    print(f"[{os.path.basename(file_path)}] 计算完成。耗时: {end_time - start_time:.2f}秒")

    return {
        "filename": os.path.basename(file_path),
        "average_scores": avg_scores,
        "sample_count": n,
        "process_time_seconds": round(end_time - start_time, 2)
        # "details": results # 如果需要每条数据的详细分数，取消注释
    }


def batch_process_directory(input_dir, output_file):
    """
    遍历处理并实时保存结果
    """
    if not os.path.exists(input_dir):
        print(f"错误：目录不存在 -> {input_dir}")
        return

    files = [f for f in os.listdir(input_dir) if f.endswith('.jsonl')]
    if not files:
        print("未找到 .jsonl 文件。")
        return

    print(f"找到 {len(files)} 个文件。结果将实时写入: {output_file}")
    print("-" * 50)

    # 这里的 output_file 建议是 .jsonl 格式，方便追加写入
    # 如果已存在，我们追加写入；如果想覆盖，请手动删除旧文件或改为 'w'

    processed_count = 0

    for filename in files:
        file_path = os.path.join(input_dir, filename)

        # 计算
        file_result = calculate_self_bleu_parallel(file_path)

        if file_result:
            # --- 核心修改：实时写入 ---
            with open(output_file, 'a+', encoding='utf-8') as f_out:
                # 写入一行 JSON 记录
                f_out.write(json.dumps(file_result, ensure_ascii=False) + "\n")

            print(f"  > 结果已保存: {filename}")

        processed_count += 1
        print("-" * 30)

    print(f"全部完成！共处理 {processed_count} 个文件。")


if __name__ == "__main__":
    # 1. 设置输入目录
    input_directory = "D:/STUDY/2026-project1/project1/main_work/计算指标/1/相似度/"

    # 2. 设置输出文件路径
    # 注意：改为 .jsonl 后缀，表示这是一个 JSON Lines 文件（每一行是一个独立的 JSON）
    # 这样方便追加写入，且读取时方便逐行读取
    output_result_file = "./all_bleu_results_fast.jsonl"

    # 如果需要重新跑，建议先删除旧的输出文件
    if os.path.exists(output_result_file):
        print("发现旧的结果文件，新结果将追加到文件末尾...")
        # os.remove(output_result_file) # 如果想每次覆盖，取消这行的注释

    # 运行
    # 必须在 if __name__ == "__main__": 下运行多进程
    batch_process_directory(input_directory, output_result_file)