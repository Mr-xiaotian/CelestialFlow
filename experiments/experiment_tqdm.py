import time
from tqdm import tqdm


def demo_tqdm_dynamic(final_total=100, sleep=0.05):
    """
    演示 tqdm 支持动态 total 与进度推进的 3 阶段过程
    阶段 1: 只增加 total，占 1/2
    阶段 2: total 和 progress 同时增加，占 1/2
    阶段 3: total 固定，只推进 progress 到 100%
    """

    third = final_total // 2  # 每阶段容量 1/2
    pbar = tqdm(total=0, desc="Dynamic tqdm demo", dynamic_ncols=True)

    # -------- Stage 1: 只增加 total --------
    target_total_stage1 = third
    while pbar.total < target_total_stage1:
        pbar.total += 1
        pbar.refresh()
        time.sleep(sleep)

    # -------- Stage 2: total 与 progress 同时增加 --------
    target_total_stage2 = third * 2
    while pbar.total < target_total_stage2:
        pbar.total += 1
        pbar.update(1)
        pbar.refresh()
        time.sleep(sleep)

    # -------- Stage 3: total 不变，只推进进度直到 total --------
    while pbar.n < pbar.total:
        pbar.update(1)
        time.sleep(sleep)

    pbar.close()


if __name__ == "__main__":
    demo_tqdm_dynamic()
