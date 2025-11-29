# pip install requests numpy matplotlib
import os, time, statistics as stats, concurrent.futures, requests, numpy as np
import matplotlib.pyplot as plt

URL = os.getenv("TARGET_URL", "https://api.github.com/rate_limit")  # or https://httpbin.org/get
REQUESTS = int(os.getenv("REQUESTS", 100))
CONCURRENCY = int(os.getenv("CONCURRENCY", 10))
TIMEOUT = float(os.getenv("TIMEOUT", 5))

session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=CONCURRENCY, pool_maxsize=CONCURRENCY)
session.mount("http://", adapter)
session.mount("https://", adapter)
headers = {}
# Optional: avoid GitHub rate limits with a token
# if os.getenv("GITHUB_TOKEN"): headers["Authorization"] = f"Bearer {os.getenv('GITHUB_TOKEN')}"


def one_call(_):
    t0 = time.perf_counter()
    try:
        r = session.get(URL, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        ok = True
    except Exception:
        ok = False
    return ok, (time.perf_counter() - t0) * 1000.0  # ms


def run():
    latencies = []
    errors = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        for ok, ms in ex.map(one_call, range(REQUESTS)):
            latencies.append(ms)
            if not ok:
                errors += 1

    lat = np.array(latencies, dtype=float)

    # ---- Text summary ----
    print(f"Requests: {REQUESTS}, Concurrency: {CONCURRENCY}, URL: {URL}")
    print(f"Errors: {errors}")
    p50 = np.percentile(lat, 50)
    p95 = np.percentile(lat, 95)
    p99 = np.percentile(lat, 99)
    print(
        f"avg: {lat.mean():.2f} ms | median(p50): {p50:.2f} ms | "
        f"p95: {p95:.2f} ms | p99 (tail): {p99:.2f} ms"
    )
    print(f"min: {lat.min():.2f} ms | max: {lat.max():.2f} ms")

    # ---- Visualization: Histogram + ECDF ----
    # 1) Histogram of latencies
    plt.figure()
    plt.hist(lat, bins="auto")  # default colors/styles
    plt.xlabel("Latency (ms)")
    plt.ylabel("Count")
    plt.title("Latency Distribution (Histogram)")

    # Add reference lines for p50/p95/p99
    for val, label in [(p50, "p50"), (p95, "p95"), (p99, "p99")]:
        plt.axvline(val, linestyle="--")
        plt.text(val, plt.ylim()[1]*0.9, label, rotation=90, va="top", ha="right")

    plt.tight_layout()

    # 2) Empirical CDF (helps visualize tail percentiles)
    plt.figure()
    lat_sorted = np.sort(lat)
    ecdf = np.arange(1, len(lat_sorted) + 1) / len(lat_sorted)
    plt.plot(lat_sorted, ecdf)
    plt.xlabel("Latency (ms)")
    plt.ylabel("ECDF")
    plt.title("Latency ECDF (Cumulative)")
    # Reference lines at p95/p99
    for val, label in [(p95, "p95"), (p99, "p99")]:
        plt.axvline(val, linestyle="--")
        plt.text(val, 0.02, label, rotation=90, va="bottom", ha="right")

    plt.tight_layout()
    plt.show()

    # Tip: If your distribution is very skewed, try log-scale on X:
    # plt.xscale("log")

if __name__ == "__main__":
    run()
