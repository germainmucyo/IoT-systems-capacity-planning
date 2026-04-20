# IoT Edge-Cloud Performance Explorer

**EECE 5642 — Data Visualization, Spring 2026**
Northeastern University — Department of Electrical & Computer Engineering

**Author:** Germain Mucyo | mucyo.g@northeastern.edu

---

## Overview

An interactive capacity planning dashboard for IoT edge-cloud systems. The tool simulates an IoT pipeline (devices → gateway → edge/cloud) using discrete-event simulation and visualizes performance tradeoffs through an interactive Dash web application.

The key questions this tool answers:
- What is the optimal fraction of tasks to route to edge vs. cloud?
- At what device count does system delay become unacceptable?
- How does the full (offloading ratio × device count) operating surface look?

---

## Repository Structure

```
.
├── app.py                  # Dash dashboard application
├── grid_simulation.py      # SimPy grid simulation → CSV
├── grid-computation.py     # Earlier simulation version
├── simulation_results.csv  # Pre-computed simulation data (110 rows)
├── Makefile                # Build automation
└── README.md
```

---

## Requirements

- Python 3.10+
- WSL (Ubuntu) or any Linux/macOS terminal

---

## Quick Start

### 1. Set up the environment
```bash
make setup
```
Creates a virtual environment at `~/iot_dashboard/venv` and installs all dependencies.

### 2. Generate simulation data
```bash
make simulate
```
Runs 1,100 SimPy simulations across the (x, M) parameter grid and saves results to `simulation_results.csv`. Takes ~5 minutes. Skips if CSV already exists.

### 3. Launch the dashboard
```bash
make run
```
Opens the app at **http://127.0.0.1:8050**

---

## Makefile Commands

| Command | Description |
|---|---|
| `make setup` | Create venv + install dependencies |
| `make simulate` | Run simulation grid (skips if CSV exists) |
| `make resimulate` | Force re-run simulation |
| `make run` | Launch Dash dashboard |
| `make clean` | Delete simulation_results.csv |
| `make reset` | Delete CSV + virtual environment |

---

## Dashboard Features

### Tab 1 — Offloading Analysis
- Mean delay, P95 delay, and throughput vs. offloading ratio x
- Confidence interval shading around each curve
- Annotated optimal x* marker
- KPI cards: optimal x*, min mean delay, P95 at optimum, throughput
- Slider to select device count M

### Tab 2 — Scaling Analysis
- Mean delay, P95 delay, and throughput vs. device count M
- Adjustable danger zone threshold line
- Automatic annotation of the M value where delay crosses threshold
- Slider to select offloading ratio x

### Tab 3 — Operating Surface Heatmap
- 2D heatmap of mean delay, P95 delay, or throughput over joint (x, M) space
- Green = low delay (safe), Red = high delay (danger)
- ★ markers identify optimal x per device count row
- Optimal operating point table for all M values

---

## Simulation Parameters

| Parameter | Value | Description |
|---|---|---|
| λᵢ | 0.02 tasks/sec | Per-device arrival rate |
| μ_gw | 5.0 tasks/sec | Gateway service rate |
| μ_edge | 3.0 tasks/sec | Edge server service rate |
| μ_cloud | 8.0 tasks/sec | Cloud server service rate |
| d_ge | 0.5s ± 0.1s | Gateway→Edge transmission delay |
| d_gc | 2.0s ± 0.1s | Gateway→Cloud transmission delay |
| Warm-up | 500s | Discarded to remove transient effects |
| Sim time | 5000s | Total simulation time per run |
| Replications | 10 | Per (x, M) combination |
| x range | 0.0 – 1.0 | Offloading ratio (step 0.1) |
| M range | 50 – 500 | Device count (step 50) |

---

## Key Findings

- The optimal offloading ratio x* is workload-dependent — it shifts from ~0.9 at M=100 to ~0.1 at M=500
- System delay remains near zero for M ≤ 250, then explodes at the queueing knee around M=275–300
- P95 tail latency grows faster than mean delay under heavy load
- Pure edge or pure cloud strategies are always suboptimal — a hybrid approach minimizes delay

---

## Dependencies

```
simpy
numpy
pandas
scipy
dash
plotly
```

Installed automatically via `make setup`.

---

## Acknowledgements

This project was developed for EECE 5642 Data Visualization at Northeastern University.

## License

MIT License — free to use and modify with attribution.
