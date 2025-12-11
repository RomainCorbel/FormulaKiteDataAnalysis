import os
import json
import pandas as pd
import numpy as np
from geopy.distance import geodesic
from datetime import datetime
from cog_analysis import load_boat_data
from IPython.display import display

def load_summary_intervals(summary_file="summary.json"):
    with open(summary_file, "r") as f:
        summary = json.load(f)
    return {r["run"]: r["intervals"] for r in summary}

def filter_interval(df, start, end):
    return df[(df["SecondsSince1970"] >= start) & (df["SecondsSince1970"] <= end)]

def load_and_reduce_boat_data(run_path, summary_dict):
    print(os.listdir(run_path))
    csv_files = sorted([f for f in os.listdir(run_path) if f.endswith(".csv")])
    if len(csv_files) < 2:
        raise ValueError("At least two CSV files are required.")

    boat1_df, boat2_df, boat1_name, boat2_name = load_boat_data(
        os.path.join(run_path, csv_files[0]),
        os.path.join(run_path, csv_files[1])
    )

    run_name = os.path.basename(run_path)
    if run_name not in summary_dict:
        raise ValueError(f"No intervals for run: {run_name}")

    intervals = summary_dict[run_name]
    if len(intervals) < 2:
        raise ValueError(f"Need at least two intervals for run: {run_name}")

    return {
        "reduced_boat1_int1_df": filter_interval(boat1_df, intervals[0]["start_time"], intervals[0]["end_time"]),
        "reduced_boat2_int1_df": filter_interval(boat2_df, intervals[0]["start_time"], intervals[0]["end_time"]),
        "reduced_boat1_int2_df": filter_interval(boat1_df, intervals[1]["start_time"], intervals[1]["end_time"]),
        "reduced_boat2_int2_df": filter_interval(boat2_df, intervals[1]["start_time"], intervals[1]["end_time"]),
        "boat1_name": boat1_name,
        "boat2_name": boat2_name
    }


def compute_stats(df, columns):
    stats = {}
    for col in columns:
        data = df[col].dropna()
        if col == "COG":
            angles = np.deg2rad(data)
            mean = np.rad2deg(np.arctan2(np.mean(np.sin(angles)), np.mean(np.cos(angles)))) % 360
            stats[col] = {"Avg": mean, "Min": data.min(), "Max": data.max(), "Count": len(data), "StdDev": data.std()}
        else:
            stats[col] = {"Avg": data.mean(), "Min": data.min(), "Max": data.max(), "Count": len(data), "StdDev": data.std()}
    return pd.DataFrame(stats).T

def compute_distance(lat, lon):
    return sum(geodesic((lat[i-1], lon[i-1]), (lat[i], lon[i])).meters for i in range(1, len(lat)))

def compute_straight_line(lat, lon):
    return geodesic((lat.iloc[0], lon.iloc[0]), (lat.iloc[-1], lon.iloc[-1])).meters if len(lat) > 1 else 0

def compare_runs(df1, df2, label1, label2):
    cols = ["TWS", "TWD", "SOG", "VMG", "COG", "TWA_Abs", "Heel_Lwd", "Trim"]
    stats1 = compute_stats(df1, cols)
    stats2 = compute_stats(df2, cols)
    dist1, dist2 = compute_distance(df1["Lat"], df1["Lon"]), compute_distance(df2["Lat"], df2["Lon"])
    straight1, straight2 = compute_straight_line(df1["Lat"], df1["Lon"]), compute_straight_line(df2["Lat"], df2["Lon"])
    summary_df = pd.DataFrame({label1: [dist1, straight1], label2: [dist2, straight2]}, index=["Distance [m]", "Straight Line [m]"])
    return stats1, stats2, summary_df

def compute_vmg_gain(df1, df2):
    ktomps = 0.51444
    vmg1_start = df1["VMG"].head(10).mean() * ktomps
    vmg2_start = df2["VMG"].head(10).mean() * ktomps
    vmg1_end = df1["VMG"].tail(10).mean() * ktomps
    vmg2_end = df2["VMG"].tail(10).mean() * ktomps
    duration = df1["SecondsSince1970"].iloc[-1] - df1["SecondsSince1970"].iloc[0]
    gain = (vmg2_end - vmg1_end) - (vmg2_start - vmg1_start)
    gain_per_min = gain / (duration / 60) if duration else float("nan")
    return pd.DataFrame([[f"{vmg2_start - vmg1_start:+.1f} m", f"{vmg2_end - vmg1_end:+.1f} m", f"{gain:+.1f} m", f"{gain_per_min:+.2f} m/min"]],
                        columns=["Begin", "End", "Gain (total)", "Gain (per Minute)"], index=["VMG"])

def merge_stats(stats1, stats2, label1, label2):
    stats1.columns = [f"{c} ({label1})" for c in stats1.columns]
    stats2.columns = [f"{c} ({label2})" for c in stats2.columns]
    return pd.concat([stats1, stats2], axis=1)

def display_all(stats, summary, gain, boat1, boat2):
    display(stats.style.format("{:.4g}").set_caption("Statistics"))
    display(summary.style.format("{:.4g}").set_caption("Distance Summary"))
    display(gain.style.set_caption(f"{boat2} gain vs {boat1}"))

def process_run(df1, df2, name1, name2):
    if df1.empty or df2.empty:
        print(f"⚠️ Skipping run {name1} vs {name2}: empty DataFrame")
        return None, None, None, name1, name2

    df1 = df1.copy()
    df2 = df2.copy()
    df1["ISODateTimeUTC"] = pd.to_datetime(df1["ISODateTimeUTC"])
    df2["ISODateTimeUTC"] = pd.to_datetime(df2["ISODateTimeUTC"])

    if df1["ISODateTimeUTC"].empty:
        print(f"⚠️ Skipping run {name1}: no ISODateTimeUTC")
        return None, None, None, name1, name2

    start_time = df1["ISODateTimeUTC"].iloc[0].ceil("min")
    df1 = df1[df1["ISODateTimeUTC"] >= start_time]
    df2 = df2[df2["ISODateTimeUTC"] >= start_time]

    stats1, stats2, summary_df = compare_runs(df1, df2, name1, name2)
    merged_stats = merge_stats(stats1, stats2, name1, name2)
    gain = compute_vmg_gain(df1, df2)
    display_all(merged_stats, summary_df, gain, name1, name2)

    return merged_stats, summary_df, gain, name1, name2

def process_all_run(run_path, summary_path):
    summary_dict = load_summary_intervals(summary_path)
    result = load_and_reduce_boat_data(run_path, summary_dict)
    full_boat1_df, full_boat2_df = result["reduced_boat1_int1_df"].copy(), result["reduced_boat2_int1_df"].copy()
    full_boat1_df["ISODateTimeUTC"] = pd.to_datetime(full_boat1_df["ISODateTimeUTC"])
    full_boat2_df["ISODateTimeUTC"] = pd.to_datetime(full_boat2_df["ISODateTimeUTC"])
    name1 = result["boat1_name"]
    name2 = result["boat2_name"]
    process_run(full_boat1_df, full_boat2_df, name1, name2)
    process_run(result["reduced_boat1_int1_df"], result["reduced_boat2_int1_df"], name1, name2)
    process_run(result["reduced_boat1_int2_df"], result["reduced_boat2_int2_df"], name1, name2)
    return compare_runs(full_boat1_df, full_boat2_df, name1, name2) + (name1, name2)
