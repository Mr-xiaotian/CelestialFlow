import time
from tqdm import tqdm


def test_tqdm_performance(use_tqdm=True, data_size=10_000_000):
    print(f"\nTesting with tqdm = {use_tqdm}, data_size = {data_size}")

    # 阶段一：数据准备
    start_prepare = time.time()
    if use_tqdm:
        pbar = tqdm(total=0, desc="Preparing and Processing", dynamic_ncols=True)
    data = []
    for i in range(data_size):
        data.append(i)
    if use_tqdm:
        pbar.total = len(data)
    end_prepare = time.time()

    # 阶段二：数据处理
    start_process = time.time()
    for item in data:
        _ = item * 2  # 模拟处理
        # time.sleep(0.00001)
        if use_tqdm:
            pbar.update(1)
    if use_tqdm:
        pbar.close()
    end_process = time.time()

    print(f"Preparation time: {end_prepare - start_prepare:.4f} seconds")
    print(f"Processing time:  {end_process - start_process:.4f} seconds")
    print(f"Total time:       {end_process - start_prepare:.4f} seconds")


if __name__ == "__main__":
    # 示例调用
    test_tqdm_performance(use_tqdm=False, data_size=1_000_000)
    test_tqdm_performance(use_tqdm=True, data_size=1_000_000)
