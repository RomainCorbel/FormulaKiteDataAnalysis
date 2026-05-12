# Formula Kite Data Analysis

This repository contains the analysis pipelines for the Formula Kite testing campaigns conducted at two locations:

- **Port Camargue, France** — June 6–11, 2025
- **Hyères, France** — November 2025

Three types of sessions are covered: straight runs (upwind and downwind speed testing), maneuvers (jibes and tacks), and race starts (Hyères only).

---

## Dataset

The raw and pre-processed data are **not stored in this repository** due to file size constraints.

- Download the dataset: **[Dataset — link to be added]**
- Once downloaded, place the `Data_Sailnjord/` folder directly inside `FormulaKiteDataAnalysis/` so that paths resolve correctly.

The expected location is:
```
FormulaKiteDataAnalysis/
└── Data_Sailnjord/        <-- place it here
```

### Data structure inside `Data_Sailnjord/`

The data was originally recorded by Sailnjord and reformatted to the following structure (standardized file names and folder hierarchy).

The structure differs slightly between the two campaigns:

**Port Camargue** — each day folder contains:
- One folder per run, each with the rider CSV files (`Gian Stragiotti.csv`, `Karl Maeder.csv`, `SenseBoard.csv`) — Vakaros telemetry: position, speed, wind, heel, line tensions
- An `Interview and equipment/` folder — one Excel file per rider with equipment setup, rider weight, mast brand, and role assignment
- A `senseboard_log/` folder — one Excel file covering the full day's SenseBoard load cell data (not split by run)

**Hyères** — same structure, but without `senseboard_log/`: the SenseBoard load cell data is already embedded directly in the rider CSV files.

```
Data_Sailnjord/
├── Port Camargue June 2025/
│   ├── Straight_lines/
│   │   ├── 06_06_2025/
│   │   │   ├── Interview and equipment/     (Interview [Name] 250606.xlsx)
│   │   │   ├── senseboard_log/              (SenseBoard_log_modified_250606.xlsx)
│   │   │   └── 06_06_2025_Run{1..8}/        (Gian Stragiotti.csv | Karl Maeder.csv | SenseBoard.csv)
│   │   ├── 07_06_2025/                      (10 runs)
│   │   ├── 09_06_2025/                      (11 runs — Karl + SenseBoard only)
│   │   └── 10_06_2025/                      (10 runs)
│   └── Maneuvers/
│       ├── 08_06_2025/
│       │   ├── Interview and equipment/
│       │   ├── senseboard_log/
│       │   └── 08_06_2025_Run{1..6}/
│       └── 11_06_2025/                      (5 runs)
│
└── Hyères November 2025/
    ├── Straight_lines/
    │   └── 25_11_2025/                      (7 runs — Gian Stragiotti.csv | Max Maeder.csv)
    ├── Maneuvers/
    │   └── 30_11_2025/                      (3 runs)
    └── Starts/
        └── 30_11_2025/                      (10 races)
```

---

## Repository Structure

```
FormulaKiteDataAnalysis/
├── Data_Sailnjord/                          # dataset (not in git — see above)
│
├── Straight Run_port_camargue/              # straight run analysis, Port Camargue
├── Straight Run_hyeres/                     # straight run analysis, Hyères
├── Straight Run_hyeres_weight_analysis/     # weight-effect specialization, Hyères
│
├── Maneuvers_port_camargue/                 # jibe and tack analysis, Port Camargue
├── Maneuvers_hyeres/                        # jibe and tack analysis, Hyères
│
├── Starts_hyeres/                           # race start analysis, Hyères
│
├── requirements.txt                         # pip dependencies
└── environment.yml                          # conda environment (name: sail2, Python 3.10)
```

Each analysis folder has its own `README.md` describing its pipeline in detail.

---

## Folder Descriptions

### `Straight Run_port_camargue/` and `Straight Run_hyeres/`

Straight run analysis for each location. The pipeline detects stable upwind/downwind intervals from the raw telemetry, enriches them with rider and equipment metadata from interview files, merges everything into a single dataset, and runs statistical analyses and reports.

Key outputs: rider speed comparisons (SOG, VMG), line tension analysis, mast type effect (Levi vs Chubanga), directional gain between riders.

See [Straight Run_port_camargue/README.md](Straight%20Run_port_camargue/README.md) and [Straight Run_hyeres/README.md](Straight%20Run_hyeres/README.md).

---

### `Straight Run_hyeres_weight_analysis/`

A variant of the Hyères straight run pipeline focused specifically on the effect of rider weight on performance. Multiple notebooks test different weight subsets (e.g., below 120 kg, between 105–120 kg) and compare SOG distributions across those groups.

See [Straight Run_hyeres_weight_analysis/README.md](Straight%20Run_hyeres_weight_analysis/README.md).

---

### `Maneuvers_port_camargue/` and `Maneuvers_hyeres/`

Maneuver analysis (jibes and tacks) for each location. The pipeline detects jibe and tack windows from COG and SOG signals, merges the data, and generates rider-specific reports with KPIs (speed loss, recovery time, heel dynamics, line loading).

At Port Camargue both Gian and Karl are analyzed. At Hyères only Gian's maneuvers are covered (limited data).

See [Maneuvers_port_camargue/README.md](Maneuvers_port_camargue/README.md) and [Maneuvers_hyeres/README.md](Maneuvers_hyeres/README.md).

---

### `Starts_hyeres/`

Race start analysis from the Hyères campaign (10 races). Computes acceleration metrics, polar ratio (actual vs reference speed), time to reach peak speed, and plots trajectories relative to wind direction.

See [Starts_hyeres/README.md](Starts_hyeres/README.md).

---

## Setup

```bash
conda env create -f environment.yml
conda activate sail2
```

Or with pip:
```bash
pip install -r requirements.txt
```

Then place the `Data_Sailnjord/` folder in the repository root and run the notebooks inside the relevant analysis folder via `runner.ipynb`.
