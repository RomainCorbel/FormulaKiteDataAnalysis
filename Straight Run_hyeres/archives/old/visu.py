import os
import json
import pandas as pd
import numpy as np
from geopy.distance import geodesic
from datetime import datetime
from cog_analysis import load_boat_data, plot_full_trajectories
from IPython.display import display

def load_summary_intervals(summary_file: str = "summary.json") -> dict:
    with open(summary_file, "r") as f:
        summary = json.load(f)
    return {r["run"]: r["intervals"] for r in summary}

def load_and_reduce_boat_data(run_path: str, summary_dict: dict):
    csv_files = [f for f in os.listdir(run_path) if f.endswith(".csv")]
    if len(csv_files) < 2:
        raise ValueError("At least two CSV files are required.")

    boat1_df, boat2_df, boat1_name, boat2_name = load_boat_data(
        os.path.join(run_path, csv_files[0]),
        os.path.join(run_path, csv_files[1])
    )

    run_name = os.path.basename(run_path)
    if run_name not in summary_dict:
        raise ValueError(f"No intervals found for run: {run_name}")

    intervals = summary_dict[run_name]
    if len(intervals) < 2:
        raise ValueError(f"Expected at least two intervals for run: {run_name}")

    def filter_interval(df, start, end):
        return df[(df["SecondsSince1970"] >= start) & (df["SecondsSince1970"] <= end)]

    return {
        "reduced_boat1_int1_df": filter_interval(boat1_df, *intervals[0].values()),
        "reduced_boat2_int1_df": filter_interval(boat2_df, *intervals[0].values()),
        "reduced_boat1_int2_df": filter_interval(boat1_df, *intervals[1].values()),
        "reduced_boat2_int2_df": filter_interval(boat2_df, *intervals[1].values()),
        "boat1_name": boat1_name,
        "boat2_name": boat2_name
    }

def load_run_data(run_path, summary_path):
    csv_files = [f for f in os.listdir(run_path) if f.endswith(".csv")]
    boat1_df, boat2_df, boat1_name, boat2_name = load_boat_data(
        os.path.join(run_path, csv_files[0]),
        os.path.join(run_path, csv_files[1])
    )
    with open(summary_path, "r") as f:
        summary = json.load(f)
    run_name = os.path.basename(run_path)
    intervals = {r["run"]: r["intervals"] for r in summary}[run_name]
    return boat1_df, boat2_df, boat1_name, boat2_name, intervals

def compute_stats(df, columns):
    stats = {}
    for col in columns:
        data = df[col].dropna()
        if col == 'COG':
            angles = np.deg2rad(data)
            mean = np.rad2deg(np.arctan2(np.mean(np.sin(angles)), np.mean(np.cos(angles)))) % 360
            stats[col] = {"Avg": mean, "Min": data.min(), "Max": data.max(), "Count": len(data), "StdDev": data.std()}
        else:
            stats[col] = {"Avg": data.mean(), "Min": data.min(), "Max": data.max(), "Count": len(data), "StdDev": data.std()}
    return pd.DataFrame(stats).T

def compute_distance_traveled(lat, lon):
    return sum(geodesic((lat[i-1], lon[i-1]), (lat[i], lon[i])).meters for i in range(1, len(lat)))

def compute_straight_line_distance(lat, lon):
    return geodesic((lat.iloc[0], lon.iloc[0]), (lat.iloc[-1], lon.iloc[-1])).meters if len(lat) >= 2 else 0

def compare_runs(df1, df2, label1="Boat1", label2="Boat2"):
    columns = ['TWS', 'TWD', 'SOG', 'VMG', 'COG', 'TWA_Abs', 'Heel_Lwd', 'Trim']
    stats1 = compute_stats(df1, columns)
    stats2 = compute_stats(df2, columns)
    dist1 = compute_distance_traveled(df1["Lat"], df1["Lon"])
    dist2 = compute_distance_traveled(df2["Lat"], df2["Lon"])
    straight1 = compute_straight_line_distance(df1["Lat"], df1["Lon"])
    straight2 = compute_straight_line_distance(df2["Lat"], df2["Lon"])
    summary_df = pd.DataFrame({label1: [dist1, straight1], label2: [dist2, straight2]},
                              index=["Distance Sailed [m]", "Start-End Straight Line [m]"])
    return stats1, stats2, summary_df

def compute_vmg_gain_simple(df1, df2):
    knot_to_mps = 0.51444
    vmg1_start = df1["VMG"].head(10).mean() * knot_to_mps
    vmg2_start = df2["VMG"].head(10).mean() * knot_to_mps
    vmg1_end = df1["VMG"].tail(10).mean() * knot_to_mps
    vmg2_end = df2["VMG"].tail(10).mean() * knot_to_mps
    duration_sec = df1["SecondsSince1970"].iloc[-1] - df1["SecondsSince1970"].iloc[0]
    gain = (vmg2_end - vmg1_end) - (vmg2_start - vmg1_start)
    duration_min = duration_sec / 60
    gain_per_min = gain / duration_min if duration_min else float("nan")
    return pd.DataFrame([[f"{vmg2_start - vmg1_start:+.1f} m", f"{vmg2_end - vmg1_end:+.1f} m", f"{gain:+.1f} m", f"{gain_per_min:+.2f} m/min"]],
                        columns=["Begin", "End", "Gain (total)", "Gain (per Minute)"], index=["VMG"])

def merge_stats_table(stats1, stats2, label1, label2):
    stats1 = stats1.rename(columns=lambda x: f"{x} ({label1})")
    stats2 = stats2.rename(columns=lambda x: f"{x} ({label2})")
    combined = pd.concat([stats1, stats2], axis=1)
    order = ["Avg", "Min", "Max", "Count", "StdDev"]
    cols = [f"{stat} ({label})" for stat in order for label in (label1, label2) if f"{stat} ({label})" in combined.columns]
    return combined[cols]

def display_all(merged_stats, summary_df, gain_table, boat1_name, boat2_name):
    display(
        merged_stats.style
        .format("{:.4g}")
        .set_caption("Run tot Statistics")
    )
    display(
        summary_df.style
        .format("{:.4g}")
        .set_caption("Résumé des distances")
    )
    display(
        gain_table.style
        .format({"VMG": "{:+.4g} m"})
        .set_caption(f"{boat1_name} gains relative to {boat2_name} in Meters")
    )

def process_run(boat1_df, boat2_df, boat1_name, boat2_name):
    boat1_df = boat1_df.copy()
    boat2_df = boat2_df.copy()
    boat1_df["ISODateTimeUTC"] = pd.to_datetime(boat1_df["ISODateTimeUTC"])
    boat2_df["ISODateTimeUTC"] = pd.to_datetime(boat2_df["ISODateTimeUTC"])
    start_time = boat1_df["ISODateTimeUTC"].iloc[0].ceil("min")
    df1 = boat1_df[boat1_df["ISODateTimeUTC"] >= start_time].copy()
    df2 = boat2_df[boat2_df["ISODateTimeUTC"] >= start_time].copy()
    stats1, stats2, summary_df = compare_runs(df1, df2, boat1_name, boat2_name)
    merged_stats = merge_stats_table(stats1, stats2, boat1_name, boat2_name)
    gain_table = compute_vmg_gain_simple(df1, df2)
    display_all(merged_stats, summary_df, gain_table, boat1_name, boat2_name)
    return merged_stats, summary_df, gain_table, boat1_name, boat2_name

def process_all_run(run_path, summary_path):
    boat1_df, boat2_df, name1, name2, _ = load_run_data(run_path, summary_path)

    # Run full
    process_run(boat1_df, boat2_df, name1, name2)

    # Run 1 & 2
    summary_dict = load_summary_intervals(summary_path)
    result = load_and_reduce_boat_data(run_path, summary_dict)
    process_run(result["reduced_boat1_int1_df"], result["reduced_boat2_int1_df"], name1, name2)
    process_run(result["reduced_boat1_int2_df"], result["reduced_boat2_int2_df"], name1, name2)

    # Return last run stats
    return compare_runs(boat1_df, boat2_df, name1, name2) + (name1, name2)

