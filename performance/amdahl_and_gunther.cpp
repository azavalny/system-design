// g++ -O2 -std=c++20 gunther_amdahl_demo.cpp -lpthread && ./a.out
#include <bits/stdc++.h>
#include <thread>
#include <atomic>
#include <mutex>
#include <barrier>
using namespace std;

// Busy work to burn CPU
static inline void busy_work(uint64_t iters, volatile uint64_t &sink) {
    uint64_t acc = 0;
    for (uint64_t i = 0; i < iters; ++i) {
        acc += (i * 48271ULL) ^ (acc >> 3);
    }
    sink = acc;
}

double seconds_since(chrono::high_resolution_clock::time_point t0){
    return chrono::duration<double>(chrono::high_resolution_clock::now()-t0).count();
}

// Theoretical curves
double amdahl(double s, int N) {
    return 1.0 / (s + (1.0 - s) / N);
}
double gunther(double alpha, double beta, int N) {
    // C(N) = N / (1 + alpha*(N-1) + beta*N*(N-1))
    return N / (1 + alpha*(N-1) + beta*N*(N-1));
}

// A tiny struct intentionally packed to the same cache line for false sharing
struct alignas(64) CacheLine64 { atomic<uint64_t> v; };
struct PackedLine {
    // 8 atomics * 8B each ~= 64B → likely share one line
    atomic<uint64_t> a0{0}, a1{0}, a2{0}, a3{0}, a4{0}, a5{0}, a6{0}, a7{0};
};

int main(int argc, char** argv) {
    // Tunables (override via CLI)
    // 1: serial fraction s
    // 2: alpha (contention via mutex loop iterations)
    // 3: beta  (coherency via shared writes scaling)
    // 4: total work (iterations)
    // 5: max threads (default 100)
    // 6: coherence_rounds per thread (default 2000)
    // 7: coherence_ops_per_round per thread (default 512)
    // 8: lock_iters per thread (default derived from alpha)
    double s      = (argc > 1) ? atof(argv[1]) : 0.10;          // 10% serial
    double alpha  = (argc > 2) ? atof(argv[2]) : 0.02;          // queue/contention param (for reference)
    double beta   = (argc > 3) ? atof(argv[3]) : 0.003;         // ↑ default β for stronger coherency drag
    uint64_t total_iters = (argc > 4) ? strtoull(argv[4], nullptr, 10) : 400'000'000ULL;
    int maxN      = (argc > 5) ? atoi(argv[5]) : 100;           // sweep up to 100 by default
    int coh_rounds= (argc > 6) ? atoi(argv[6]) : 2000;          // barrier-synced bursts
    int coh_ops   = (argc > 7) ? atoi(argv[7]) : 512;           // ops per round
    int lock_iters= (argc > 8) ? atoi(argv[8]) : int(100 + 500*alpha); // scale with alpha

    cout.setf(std::ios::fixed); cout << setprecision(3);
    cout << "# Params: s="<<s<<" alpha="<<alpha<<" beta="<<beta
         <<" total_iters="<<total_iters<<" max_threads="<<maxN
         <<" coh_rounds="<<coh_rounds<<" coh_ops="<<coh_ops
         <<" lock_iters="<<lock_iters<<"\n";
    cout << "N\tSpeedup_meas\tSpeedup_amdahl\tSpeedup_gunther\tTime_s\n";

    auto run_with = [&](int N){
        uint64_t serial_iters   = static_cast<uint64_t>(total_iters * s);
        uint64_t parallel_iters = total_iters - serial_iters;

        volatile uint64_t sink1 = 0;
        auto t0 = chrono::high_resolution_clock::now();
        // --- Serial portion ---
        busy_work(serial_iters, sink1);

        // --- Parallel portion ---
        vector<thread> ts;
        mutex m; // contention (alpha-like)
        CacheLine64 hot; hot.v.store(0, memory_order_relaxed);
        PackedLine packed; // multiple atomics on same line

        // Dynamic barrier to synchronize coherence bursts (amplifies invalidations)
        std::barrier sync_point(N);

        // Divide CPU work
        uint64_t per = parallel_iters / N;
        volatile uint64_t sink2 = 0;

        for (int i=0;i<N;i++){
            ts.emplace_back([&,i]{
                // CPU work
                busy_work(per, sink2);

                // ===== Coherence bursts (β-like) =====
                // 1) All threads hit the same atomic in tight phases
                for (int r=0; r<coh_rounds; ++r){
                    sync_point.arrive_and_wait(); // align bursts to maximize invalidations
                    for (int k=0; k<coh_ops; ++k){
                        hot.v.fetch_add(1, memory_order_seq_cst);
                    }
                    // 2) Also hammer a set of atomics that live on one cache line (false sharing)
                    for (int k=0; k<coh_ops; ++k){
                        switch (k & 7) {
                            case 0: packed.a0.fetch_add(1, memory_order_seq_cst); break;
                            case 1: packed.a1.fetch_add(1, memory_order_seq_cst); break;
                            case 2: packed.a2.fetch_add(1, memory_order_seq_cst); break;
                            case 3: packed.a3.fetch_add(1, memory_order_seq_cst); break;
                            case 4: packed.a4.fetch_add(1, memory_order_seq_cst); break;
                            case 5: packed.a5.fetch_add(1, memory_order_seq_cst); break;
                            case 6: packed.a6.fetch_add(1, memory_order_seq_cst); break;
                            case 7: packed.a7.fetch_add(1, memory_order_seq_cst); break;
                        }
                    }
                }

                // ===== Contention/queuing via a tiny critical section (α-like) =====
                for (int k=0; k<lock_iters; ++k){
                    lock_guard<mutex> lg(m);
                    // tiny critical section intentionally empty
                }
            });
        }
        for (auto &t: ts) t.join();

        return seconds_since(t0);
    };

    // Baseline (N=1)
    double t1 = run_with(1);

    for (int N=1; N<=maxN; ++N){
        double tN   = (N==1)? t1 : run_with(N);
        double meas = t1 / tN;

        // The β, α used in the theoretical lines are the CLI ones; they won’t
        // exactly equal the synthetic work, but the curve should qualitatively match.
        cout << N << "\t" << meas
             << "\t\t" << amdahl(s,N)
             << "\t\t" << gunther(alpha,beta,N)
             << "\t\t" << tN << "\n";
    }
    return 0;
}
