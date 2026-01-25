# free_threading_bench.py
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def count_primes(start: int, end: int) -> int:
    # Pure-Python, CPU-bound work (good for showing GIL vs free-threading)
    c = 0
    for x in range(start, end):
        c += 1 if is_prime(x) else 0
    return c


def run_single(total_start: int, total_end: int) -> int:
    return count_primes(total_start, total_end)


def run_threads(total_start: int, total_end: int, workers: int) -> int:
    span = total_end - total_start
    chunk = span // workers
    ranges = []
    s = total_start
    for i in range(workers):
        e = total_end if i == workers - 1 else s + chunk
        ranges.append((s, e))
        s = e

    with ThreadPoolExecutor(max_workers=workers) as ex:
        return sum(ex.map(lambda r: count_primes(r[0], r[1]), ranges))


def timed(label: str, fn):
    t0 = time.perf_counter()
    out = fn()
    dt = time.perf_counter() - t0
    print(f"{label:>18}: {dt:8.3f}s  (result={out})")
    return dt


def main():
    print(sys.version)
    gil_enabled = getattr(sys, "_is_gil_enabled", lambda: None)()
    print(f"GIL enabled? {gil_enabled}")  # False on free-threaded build :contentReference[oaicite:4]{index=4}

    # Tune this range if needed:
    total_start = 10_000
    total_end = 250_000

    workers_list = [1, 2, 4, 8, os.cpu_count() or 8]

    base = timed("single-thread", lambda: run_single(total_start, total_end))
    print()

    for w in workers_list:
        dt = timed(f"threads x{w}", lambda w=w: run_threads(total_start, total_end, w))
        speedup = base / dt
        print(f"{'':>18}  speedup: {speedup:5.2f}x\n")


if __name__ == "__main__":
    main()
