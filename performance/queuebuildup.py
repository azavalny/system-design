# asyncio M/M/1-ish toy: when λ > μ, the queue explodes; when λ < μ, it stabilizes
import asyncio, random, time
from collections import deque
import numpy as np
import matplotlib.pyplot as plt

ARRIVAL_EVERY_SEC = 0.01   # λ ≈ 100 req/s
SERVICE_MEAN_SEC  = 0.02   # μ ≈ 50 req/s  (intentionally slower ⇒ backlog)
DURATION_SEC      = 5
MONITOR_EVERY_SEC = 0.01

queue = asyncio.Queue()
wait_times = []
queue_lengths_over_time = deque(maxlen=50_000)  # (timestamp, qsize) tuples

async def producer():
    t_end = time.time() + DURATION_SEC
    while time.time() < t_end:
        await queue.put(time.time())   # enqueue job with "arrival timestamp"
        await asyncio.sleep(ARRIVAL_EVERY_SEC)

async def consumer(name):
    while True:
        arrival_ts = await queue.get()
        # simulate service time ~ exponential
        svc = random.expovariate(1.0 / SERVICE_MEAN_SEC)
        await asyncio.sleep(svc)
        wait_times.append(time.time() - arrival_ts)  # includes waiting + service
        queue.task_done()

async def monitor():
    t0 = time.time()
    t_end = t0 + DURATION_SEC
    while time.time() < t_end:
        queue_lengths_over_time.append((time.time() - t0, queue.qsize()))
        await asyncio.sleep(MONITOR_EVERY_SEC)
    # capture one last point at the end of production window
    queue_lengths_over_time.append((time.time() - t0, queue.qsize()))

async def main():
    cons = [asyncio.create_task(consumer(f"C{i}")) for i in range(1)]  # 1 server
    tasks = [asyncio.create_task(producer()), asyncio.create_task(monitor())]
    await asyncio.gather(*tasks)
    await queue.join()  # drain remaining
    for c in cons:
        c.cancel()

    if wait_times:
        lat = np.array(wait_times, dtype=float) * 1000.0  # ms
        p50 = np.percentile(lat, 50)
        p95 = np.percentile(lat, 95)
        p99 = np.percentile(lat, 99)
        print(f"Jobs: {len(lat)} | avg: {lat.mean():.1f} ms | p50: {p50:.1f} ms | p95: {p95:.1f} ms | p99: {p99:.1f} ms")
        print(f"min: {lat.min():.1f} ms | max: {lat.max():.1f} ms")
    else:
        lat = np.array([])

    peak_q = max((q for _, q in queue_lengths_over_time), default=0)
    print(f"Final queue length: {queue.qsize()} | Peak queue length: {peak_q}")

    # ======== Visualizations ========
    # 1) Queue length over time
    if queue_lengths_over_time:
        t, q = zip(*queue_lengths_over_time)
        plt.figure()
        plt.plot(t, q)
        plt.xlabel("Time since start (s)")
        plt.ylabel("Queue length (jobs)")
        plt.title("Queue Length Over Time")
        plt.grid(True, linewidth=0.3)
        plt.tight_layout()
        # plt.savefig("queue_length_over_time.png", dpi=150)

    # 2) Histogram of total time (wait + service)
    if lat.size > 0:
        plt.figure()
        plt.hist(lat, bins="auto")
        plt.xlabel("Total time per job (ms)")
        plt.ylabel("Count")
        plt.title("Total Time Distribution (Histogram)")
        # reference lines
        for val, label in [(np.percentile(lat, 50), "p50"), (np.percentile(lat, 95), "p95"), (np.percentile(lat, 99), "p99")]:
            plt.axvline(val, linestyle="--")
            ymax = plt.ylim()[1]
            plt.text(val, ymax*0.9, label, rotation=90, va="top", ha="right")
        plt.grid(True, linewidth=0.3)
        plt.tight_layout()
        # plt.savefig("total_time_hist.png", dpi=150)

        # 3) ECDF of total time (great for tails)
        plt.figure()
        lat_sorted = np.sort(lat)
        ecdf = np.arange(1, lat_sorted.size + 1) / lat_sorted.size
        plt.plot(lat_sorted, ecdf)
        plt.xlabel("Total time per job (ms)")
        plt.ylabel("ECDF")
        plt.title("Total Time ECDF")
        for val, label in [(np.percentile(lat, 95), "p95"), (np.percentile(lat, 99), "p99")]:
            plt.axvline(val, linestyle="--")
            plt.text(val, 0.02, label, rotation=90, va="bottom", ha="right")
        plt.grid(True, linewidth=0.3)
        plt.tight_layout()
        # plt.savefig("total_time_ecdf.png", dpi=150)

    plt.show()

if __name__ == "__main__":
    asyncio.run(main())
