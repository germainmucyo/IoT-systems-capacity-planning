"""
grid_simulation.py
Sweeps (x, M) parameter space using discrete-event simulation (SimPy).
Saves results to simulation_results.csv for use in the Dash dashboard.

Parameters varied:
  x  — offloading ratio (fraction of tasks sent to edge)
  M  — number of IoT devices

Output columns:
  x, M, mean_delay, p95_delay, throughput,
  ci_mean_low, ci_mean_high, ci_p95_low, ci_p95_high
"""

import simpy
import numpy as np
import pandas as pd
from scipy import stats
import itertools

# ── Simulation parameters ────────────────────────────────────────────────────
LAMBDA_I      = 0.02   # per-device arrival rate (tasks/sec)
MU_GW         = 5.0    # gateway service rate (tasks/sec)
MU_EDGE       = 3.0    # edge server service rate (tasks/sec)
MU_CLOUD      = 8.0    # cloud server service rate (tasks/sec)
D_GE_BASE     = 0.5    # gateway→edge base transmission delay (sec)
D_GC_BASE     = 2.0    # gateway→cloud base transmission delay (sec)
JITTER        = 0.1    # uniform jitter range ±j (sec)

SIM_TIME      = 5000   # total simulation time per run (sec)
WARMUP        = 500    # warm-up period to discard (sec)
N_REPS        = 10     # replications per (x, M) combination
CONFIDENCE    = 0.95   # confidence interval level

# ── Parameter grid ────────────────────────────────────────────────────────────
X_VALUES = np.round(np.arange(0.0, 1.1, 0.1), 2)   # 0.0, 0.1, ..., 1.0
M_VALUES = [50, 100, 150, 200, 250, 300, 350, 400, 450, 500]


# ── SimPy simulation ──────────────────────────────────────────────────────────

class IoTSystem:
    def __init__(self, env, x, lam_total, rng):
        self.env       = env
        self.x         = x
        self.lam_total = lam_total
        self.rng       = rng

        # Single-server resources
        self.gateway = simpy.Resource(env, capacity=1)
        self.edge    = simpy.Resource(env, capacity=1)
        self.cloud   = simpy.Resource(env, capacity=1)

        # Collect (arrival_time, completion_time) for steady-state tasks
        self.completed = []

    def run(self):
        self.env.process(self._source())

    def _source(self):
        """Generate tasks according to Poisson process (exponential inter-arrivals)."""
        while True:
            inter = self.rng.exponential(1.0 / self.lam_total)
            yield self.env.timeout(inter)
            arrival = self.env.now
            self.env.process(self._task(arrival))

    def _task(self, arrival):
        # ── Gateway ──────────────────────────────────────────────────────────
        with self.gateway.request() as req:
            yield req
            yield self.env.timeout(self.rng.exponential(1.0 / MU_GW))

        # ── Routing decision ─────────────────────────────────────────────────
        go_edge = self.rng.random() < self.x

        if go_edge:
            delay = D_GE_BASE + self.rng.uniform(-JITTER, JITTER)
            delay = max(0.0, delay)
            yield self.env.timeout(delay)
            with self.edge.request() as req:
                yield req
                yield self.env.timeout(self.rng.exponential(1.0 / MU_EDGE))
        else:
            delay = D_GC_BASE + self.rng.uniform(-JITTER, JITTER)
            delay = max(0.0, delay)
            yield self.env.timeout(delay)
            with self.cloud.request() as req:
                yield req
                yield self.env.timeout(self.rng.exponential(1.0 / MU_CLOUD))

        # ── Record only steady-state completions ─────────────────────────────
        completion = self.env.now
        if arrival >= WARMUP:
            self.completed.append((arrival, completion))


def run_one(x, M, seed):
    """Run a single replication; return (mean_delay, p95_delay, throughput)."""
    rng = np.random.default_rng(seed)
    env = simpy.Environment()
    sys = IoTSystem(env, x=x, lam_total=M * LAMBDA_I, rng=rng)
    sys.run()
    env.run(until=SIM_TIME)

    if len(sys.completed) < 10:
        return np.nan, np.nan, np.nan

    arrivals, completions = zip(*sys.completed)
    delays     = np.array(completions) - np.array(arrivals)
    mean_delay = np.mean(delays)
    p95_delay  = np.percentile(delays, 95)
    throughput = len(delays) / (SIM_TIME - WARMUP)
    return mean_delay, p95_delay, throughput


# ── Grid sweep ────────────────────────────────────────────────────────────────

def compute_grid():
    rows = []
    grid = list(itertools.product(X_VALUES, M_VALUES))
    total = len(grid)

    for i, (x, M) in enumerate(grid, 1):
        print(f"[{i:>3}/{total}]  x={x:.1f}  M={M}", flush=True)

        rep_mean, rep_p95, rep_tput = [], [], []
        for rep in range(N_REPS):
            seed = int(x * 1000) + M * 100 + rep   # deterministic but varied
            md, p95, tput = run_one(x, M, seed)
            if not np.isnan(md):
                rep_mean.append(md)
                rep_p95.append(p95)
                rep_tput.append(tput)

        def ci(data):
            if len(data) < 2:
                return np.nan, np.nan
            lo, hi = stats.t.interval(
                CONFIDENCE, df=len(data)-1,
                loc=np.mean(data), scale=stats.sem(data)
            )
            return lo, hi

        m_lo, m_hi   = ci(rep_mean)
        p_lo, p_hi   = ci(rep_p95)

        rows.append({
            "x":           x,
            "M":           M,
            "mean_delay":  np.mean(rep_mean),
            "p95_delay":   np.mean(rep_p95),
            "throughput":  np.mean(rep_tput),
            "ci_mean_low":  m_lo,
            "ci_mean_high": m_hi,
            "ci_p95_low":   p_lo,
            "ci_p95_high":  p_hi,
        })

    df = pd.DataFrame(rows)
    df.to_csv("simulation_results.csv", index=False)
    print("\nDone. Results saved to simulation_results.csv")
    print(df.describe())
    return df


if __name__ == "__main__":
    compute_grid()