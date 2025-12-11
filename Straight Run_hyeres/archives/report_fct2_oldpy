import os
import json
import pandas as pd
import numpy as np
from geopy.distance import geodesic
from datetime import datetime
from cog_analysis import load_boat_data
from IPython.display import display
import matplotlib.pyplot as plt
import seaborn as sns
import pprint as pp

def load_summary_intervals(summary_file="summary.json"):
    with open(summary_file, "r") as f:
        return {r["run"]: r["intervals"] for r in json.load(f)}

def filter_interval(df, start, end):
    return df[(df["SecondsSince1970"] >= start) & (df["SecondsSince1970"] <= end)].reset_index(drop=True)

def compute_stats(df, columns):
    stats = {}
    for col in columns:
        data = df[col].dropna()
        if data.empty:
            continue
        if col == "COG":
            mean = _circular_mean(data)
        else:
            mean = data.mean()
        stats[col] = {
            "Avg": mean,
            "Min": data.min(),
            "Max": data.max(),
            "Count": len(data),
            "StdDev": data.std()
        }
    return pd.DataFrame(stats).T

def compute_distance_series(lat_series, lon_series, straight=False):
    if len(lat_series) < 2:
        return 0
    start = (lat_series.iloc[0], lon_series.iloc[0])
    end = (lat_series.iloc[-1], lon_series.iloc[-1])
    if straight:
        return geodesic(start, end).meters
    return sum(
        geodesic((lat_series.iloc[i - 1], lon_series.iloc[i - 1]),
                 (lat_series.iloc[i], lon_series.iloc[i])).meters
        for i in range(1, len(lat_series))
    )

def _circular_mean(angles):
    rad = np.radians(angles)
    return np.degrees(np.arctan2(np.mean(np.sin(rad)), np.mean(np.cos(rad)))) % 360

def _angle_to_vector(angle_deg):
    rad = np.radians(angle_deg)
    return np.array([np.sin(rad), np.cos(rad)])

def _to_meters(lat, lon, ref_lat, ref_lon):
    dx = (lon - ref_lon) * 111319.9 * np.cos(np.radians(ref_lat))
    dy = (lat - ref_lat) * 111319.9
    return np.array([dx, dy])

def _empty_result():
    return pd.DataFrame(
        [[np.nan]*3]*4,
        index=['Initial Deficit', 'Final Deficit', 'Total Gain', 'Gain per Minute'],
        columns=['Forward', 'Lateral', 'VMG']
    )

# --- Core Analysis Functions ---
import numpy as np
import pandas as pd

def compute_directional_gain(df1, df2):
    if df1.empty or df2.empty or len(df1) < 2 or len(df2) < 2:
        return _empty_result()

    try:
        cog = _circular_mean(df1["COG"].dropna())
        twd = _circular_mean(df1["TWD"].dropna())

        forward_vec = _angle_to_vector(cog)
        perp_vec = np.array([-forward_vec[1], forward_vec[0]])
        vmg_vec = _angle_to_vector(twd)
        wind_sign = np.sign(np.dot(vmg_vec, perp_vec)) or 1

        ref_lat, ref_lon = df2["Lat"].iloc[0], df2["Lon"].iloc[0]
        pos1_start = _to_meters(df1["Lat"].iloc[0], df1["Lon"].iloc[0], ref_lat, ref_lon)
        pos1_end = _to_meters(df1["Lat"].iloc[-1], df1["Lon"].iloc[-1], ref_lat, ref_lon)
        pos2_start = _to_meters(df2["Lat"].iloc[0], df2["Lon"].iloc[0], ref_lat, ref_lon)
        pos2_end = _to_meters(df2["Lat"].iloc[-1], df2["Lon"].iloc[-1], ref_lat, ref_lon)

        initial_rel = pos1_start - pos2_start
        final_rel = pos1_end - pos2_end
        # progress = initial_rel - final_rel
        progress = final_rel - initial_rel
        duration_min = (df1["SecondsSince1970"].iloc[-1] - df1["SecondsSince1970"].iloc[0]) / 60 or np.nan

        def calc_gain(vec, sign=1):
            start_deficit = -sign * np.dot(initial_rel, vec)
            end_deficit = -sign * np.dot(final_rel, vec)
            gain = sign * np.dot(progress, vec)
            return [start_deficit, end_deficit, gain, gain / duration_min]

        return pd.DataFrame({
            "Forward": calc_gain(forward_vec),
            "Lateral": calc_gain(perp_vec, wind_sign),
            "VMG": calc_gain(vmg_vec)
        }, index=['Initial Deficit', 'Final Deficit', 'Total Gain', 'Gain per Minute'])

    except Exception as e:
        print(f"Error computing directional gain: {e}")
        return _empty_result()

def merge_stats(stats1, stats2, label1, label2):
    stats1 = stats1.rename(columns=lambda x: f"{x} ({label1})")
    stats2 = stats2.rename(columns=lambda x: f"{x} ({label2})")
    combined = pd.concat([stats1, stats2], axis=1)
    order = ["Avg", "Min", "Max", "Count", "StdDev"]
    cols = [f"{stat} ({label})" for stat in order for label in (label1, label2) if f"{stat} ({label})" in combined.columns]
    return combined[cols]

def display_all(merged_stats, summary_df, gain_table, boat1_name, boat2_name):
    # Identifier les colonnes numériques pour le formatage
    numeric_cols = merged_stats.select_dtypes(include=[np.number]).columns
    styled = style_comparative_wins(merged_stats, boat1_name, boat2_name)
    styled = styled.format({col: "{:.4g}" for col in merged_stats.select_dtypes(include=[np.number]).columns})
    styled = styled.set_caption("Run Statistics")
    display(styled)

    # Use more significant digits for the percentage column and limit the distances to 1 decimal place
    summary_df = (summary_df
                .style
                .format({
                    "Distance [m]": "{:.1f}",
                    "Straight Line [m]": "{:.1f}",
                    "Distance as Percentage of Straight Line [%]": "{:.4f}",
                })
                .set_caption("Distance Summary"))
    display(summary_df)


    # Function to color negative values in red and positive values in green
    def color_negative_red(val):
        color = 'red' if val < 0 else 'green'
        return f'color: {color}'

    # Function to apply color styling only to specific rows based on row names (index)
    def color_gain(row):
        # Here row is a Series representing the row, and row.name will be the index
        if row.name in ["Total Gain", "Gain per Minute"]:  
            return [color_negative_red(x) for x in row]  # Apply color to all columns in this row
        return [""] * len(row)  # No color for other rows

    # Apply row-wise styling to 'gain_table' only for "Total Gain" and "Gain per minute" rows
    styled_gain = gain_table.style.apply(color_gain, axis=1)  # axis=1 applies the function row-wise
    styled_gain = styled_gain.set_caption(f"Gain of {boat1_name} with respect to {boat2_name}")
    display(styled_gain)  # Display the styled table for gain_table

def load_and_reduce_boat_data(run_path, summary_dict):
    import copy

    csv_files = sorted(f for f in os.listdir(run_path) if f.endswith(".csv"))
    if len(csv_files) < 2:
        raise ValueError("At least two CSV files are required.")

    df1, df2, name1, name2 = load_boat_data(
        os.path.join(run_path, csv_files[0]),
        os.path.join(run_path, csv_files[1])
    )
    if df1.empty or df2.empty:
        raise ValueError("One or both boat DataFrames are empty")

    run_name = os.path.basename(run_path)
    intervals = copy.deepcopy(summary_dict.get(run_name))
    if not intervals or len(intervals) < 2:
        raise ValueError(f"No or insufficient intervals for run: {run_name}")

    # --- Ensure boat1 is always the master (boat1_master_leeward == True) ---
    if not intervals[0]["boat1_master_leeward"]:
        # Swap DataFrames
        df1, df2 = df2, df1
        name1, name2 = name2, name1
        """
        # Swap interval metadata
        for interval in intervals:
            keys_to_swap = [
                "boat1_name", "boat2_name",
                "avg_SOG_boat1", "avg_SOG_boat2",
                "SOG_variation_boat1", "SOG_variation_boat2",
                "avg TWA boat1", "avg TWA boat2",
                "boat1_total_weight", "boat2_total_weight",
                "boat1_master_leeward", "boat2_master_leeward"
            ]
            for key in keys_to_swap:
                if "boat1" in key:
                    boat1_key = key
                    boat2_key = key.replace("boat1", "boat2")
                else:
                    boat2_key = key
                    boat1_key = key.replace("boat2", "boat1")

                interval[boat1_key], interval[boat2_key] = interval[boat2_key], interval[boat1_key]
            """
    return {
        "full_df1": df1,
        "full_df2": df2,
        "reduced_boat1_int1_df": filter_interval(df1, intervals[0]["start_time"], intervals[0]["end_time"]),
        "reduced_boat2_int1_df": filter_interval(df2, intervals[0]["start_time"], intervals[0]["end_time"]),
        "reduced_boat1_int2_df": filter_interval(df1, intervals[1]["start_time"], intervals[1]["end_time"]),
        "reduced_boat2_int2_df": filter_interval(df2, intervals[1]["start_time"], intervals[1]["end_time"]),
        "boat1_name": name1,
        "boat2_name": name2
    }




def compare_runs(df1, df2, label1, label2):
    cols = ["TWS", "TWD", "SOG", "VMG", "COG", "TWA_Abs", "Heel_Lwd", "side_line2", "Line_C", "total_line2"]
    stats1 = compute_stats(df1, cols)
    stats2 = compute_stats(df2, cols)
    dist1 = compute_distance_series(df1["Lat"], df1["Lon"])
    dist2 = compute_distance_series(df2["Lat"], df2["Lon"])
    straight1 = compute_distance_series(df1["Lat"], df1["Lon"], straight=True)
    straight2 = compute_distance_series(df2["Lat"], df2["Lon"], straight=True)
    pct_dist1 = (dist1 / straight1 * 100) if straight1 != 0 else np.nan
    pct_dist2 = (dist2 / straight2 * 100) if straight2 != 0 else np.nan
    summary = pd.DataFrame({
        label1: [dist1, straight1, pct_dist1],
        label2: [dist2, straight2, pct_dist2]
    }, index=["Distance [m]", "Straight Line [m]", "Distance as Percentage of Straight Line [%]"])
    
    return stats1, stats2, summary

def add_winner_columns(merged_stats, name1, name2):
    rules = {
        "SOG": {"Avg": "max", "StdDev": "min"},
        "VMG": {"Avg": "max", "StdDev": "min"},
        "COG": {"StdDev": "min"},
        "Heel_Lwd": {"Avg": "max", "StdDev": "min"},
        "Total_lines": {"Avg": "max", "StdDev": "min"},
        "Side_lines": {"Avg": "max", "StdDev": "min"},
        "Line_C": {"Avg": "max", "StdDev": "min"},
    }

    winner_avg = []
    winner_std = []
    winner_overall = []

    for index in merged_stats.index:
        rule = rules.get(index, {})
        scores = {name1: 0, name2: 0}

        avg_win, std_win = "", ""

        # Avg rule
        decisive_avg = "Avg" in rule
        if decisive_avg:
            col1 = f"Avg ({name1})"
            col2 = f"Avg ({name2})"
            if col1 in merged_stats.columns and col2 in merged_stats.columns:
                val1 = merged_stats.at[index, col1]
                val2 = merged_stats.at[index, col2]
                if pd.notna(val1) and pd.notna(val2):
                    if rule["Avg"] == "max":
                        avg_win = name1 if val1 > val2 else name2
                    else:
                        avg_win = name1 if val1 < val2 else name2
                    scores[avg_win] += 1

        # StdDev rule
        decisive_std = "StdDev" in rule
        if decisive_std:
            col1 = f"StdDev ({name1})"
            col2 = f"StdDev ({name2})"
            if col1 in merged_stats.columns and col2 in merged_stats.columns:
                val1 = merged_stats.at[index, col1]
                val2 = merged_stats.at[index, col2]
                if pd.notna(val1) and pd.notna(val2):
                    std_win = name1 if val1 < val2 else name2
                    scores[std_win] += 1

        # Final Overall Decision
        if scores[name1] > scores[name2]:
            overall = name1
        elif scores[name2] > scores[name1]:
            overall = name2
        elif scores[name1] == scores[name2] == 0:
            overall = ""
        else:
            overall = "Tie"

        # Format: decisive wins unmarked, non-decisive in parentheses
        winner_avg.append(avg_win if decisive_avg else f"({avg_win})" if avg_win else "")
        winner_std.append(std_win if decisive_std else f"({std_win})" if std_win else "")
        winner_overall.append(overall)

    merged_stats["Winner (Avg)"] = winner_avg
    merged_stats["Winner (StdDev)"] = winner_std
    merged_stats["Winner (Overall)"] = winner_overall

    return merged_stats

def style_comparative_wins(df, name1, name2):
    rules = {
        "SOG": {"Avg": "max", "StdDev": "min"},
        "VMG": {"Avg": "max", "StdDev": "min"},
        "COG": {"StdDev": "min"},
        "Heel_Lwd": {"Avg": "max", "StdDev": "min"},
        "Total_lines": {"Avg": "max", "StdDev": "min"},
        "Side_lines": {"Avg": "max", "StdDev": "min"},
        "Line_C": {"Avg": "max", "StdDev": "min"},
    }
def style_comparative_wins(df, name1, name2):
    rules = {
        "SOG": {"Avg": "max", "StdDev": "min"},
        "VMG": {"Avg": "max", "StdDev": "min"},
        "COG": {"StdDev": "min"},
        "Heel_Lwd": {"Avg": "max", "StdDev": "min"},
        "Total_lines": {"Avg": "max", "StdDev": "min"},
        "Side_lines": {"Avg": "max", "StdDev": "min"},
        "Line_C": {"Avg": "max", "StdDev": "min"},
    }

    def highlight(row):
        styles = [""] * len(row)
        index = row.name  # Get the metric's row index
        rule = rules.get(index, {})

        for metric, pref in rule.items():
            col1 = f"{metric} ({name1})"
            col2 = f"{metric} ({name2})"
            
            if col1 in df.columns and col2 in df.columns:
                val1 = row[col1]
                val2 = row[col2]
                
                if pd.notna(val1) and pd.notna(val2):
                    if pref == "max":  # The higher value is better
                        if val1 > val2:
                            styles[df.columns.get_loc(col1)] = "color: green"
                            styles[df.columns.get_loc(col2)] = "color: red"
                        elif val1 < val2:
                            styles[df.columns.get_loc(col2)] = "color: green"
                            styles[df.columns.get_loc(col1)] = "color: red"
                    elif pref == "min":  # The lower value is better
                        if val1 < val2:
                            styles[df.columns.get_loc(col1)] = "color: green"
                            styles[df.columns.get_loc(col2)] = "color: red"
                        elif val1 > val2:
                            styles[df.columns.get_loc(col2)] = "color: green"
                            styles[df.columns.get_loc(col1)] = "color: red"
        return styles

    return df.style.apply(highlight, axis=1)

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


def plots(df1, df2, name1, name2, title):
    # List of columns to plot
    columns_to_plot = [
        'SOG', 'Heel_Abs', 'Heel_Lwd', 'Lat',
        'Leg', 'Line_C', 'Line_L', 'Line_R', 'Log', 'LogAlongCourse', 'Lon', 'ROT', 
        'Side_lines', 'Total_lines', 'Trim', 'TWA_Abs', 
        'VMC', 'VMG', 'Heel', 'COG', 
        'TWD', 'TWS', 'TWA'
    ]

    # Calculate the number of rows and columns for subplots
    n_columns = 8  # Set the number of columns
    n_rows = (len(columns_to_plot) + n_columns - 1) // n_columns  # Calculate number of rows to fit all subplots

    # Create subplots dynamically based on number of metrics
    fig, axes = plt.subplots(n_rows, n_columns, figsize=(25, n_rows * 3))  # Adjust figsize to be more compact
    axes = axes.flatten()  # Flatten to easily iterate

    # Convert 'ISODateTimeUTC' to seconds since the epoch for both dataframes
    df1['ISODateTimeUTC'] = pd.to_datetime(df1['ISODateTimeUTC']).dt.tz_localize(None)  # Remove timezone if present
    df2['ISODateTimeUTC'] = pd.to_datetime(df2['ISODateTimeUTC']).dt.tz_localize(None)  # Remove timezone if present

    # Convert to seconds since the epoch
    df1['SecondsSince1970'] = (df1['ISODateTimeUTC'] - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
    df2['SecondsSince1970'] = (df2['ISODateTimeUTC'] - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')

    # Define start_time as the first timestamp from df1 (or df2)
    start_time = df1['SecondsSince1970'].iloc[0]

    # Iterate over all the columns and create a subplot for each
    for i, col in enumerate(columns_to_plot):
        ax = axes[i]
        sns.lineplot(data=df1, x=df1["SecondsSince1970"] - start_time, y=col, label=f"{name1} {col}", color='blue', ax=ax, legend=False, errorbar=None)
        sns.lineplot(data=df2, x=df2["SecondsSince1970"] - start_time, y=col, label=f"{name2} {col}", color='orange', ax=ax, legend=False, errorbar=None)
        ax.set_xlabel("t", fontsize=10)
        ax.set_ylabel(col, fontsize=10)
        ax.set_aspect('auto')  # Avoid forcing square aspect ratio, let data fit better
        ax.grid(True, which='both')

    # Set a single title for the entire figure
    fig.suptitle(f"{title} - Parameters over time", fontsize=16)

    # Adjust layout to prevent overlap
    plt.tight_layout()

    # Adjust the space for the main title and make room for a single legend
    plt.subplots_adjust(top=0.93, bottom=0.07, hspace=0.3, wspace=0.3)

    # Create a single legend for the entire figure
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=3, fontsize=12, bbox_to_anchor=(0.5, -0.05))

    plt.show()
"""    
def process_run(df1, df2, name1, name2, title):
    if df1.empty or df2.empty:
        print(f"⚠️ Skipping {title} due to empty data: {name1} vs {name2}")
        return

    print("\n" + "="*80)
    print(title)
    print("="*80)

    stats1, stats2, summary = compare_runs(df1, df2, name1, name2)
    merged = merge_stats(stats1, stats2, name1, name2)
    gain = compute_directional_gain(df1, df2)
    merged = add_winner_columns(merged, name1, name2)
    display_all(merged, summary, gain, name1, name2)
    plots(df1, df2, name1, name2, title)"""

def process_run(df1, df2, name1, name2, title):
    if df1.empty or df2.empty:
        print(f"⚠️ Skipping {title} due to empty data: {name1} vs {name2}")
        return

    print("\n" + "="*80)
    print(title)
    print("="*80)

    stats1, stats2, summary = compare_runs(df1, df2, name1, name2)
    merged = merge_stats(stats1, stats2, name1, name2)
    gain = compute_directional_gain(df1, df2)
    merged = add_winner_columns(merged, name1, name2)
    display_all(merged, summary, gain, name1, name2)
    plots(df1, df2, name1, name2, title)
    return gain, merged

"""def process_all_run(run_path, summary_path, tot=False, onlyUpwind=False, onlyDownwind=False):
    summary_dict = load_summary_intervals(summary_path)
    data = load_and_reduce_boat_data(run_path, summary_dict)
    name1, name2 = data["boat1_name"], data["boat2_name"]

    run_name = os.path.basename(run_path)
    print("\n\n\n\n" + "=" * 80)
    print(f"Processing run: {run_name}")
    print("=" * 80 + "\n")

    if tot:
        print("Processing total run (full data)...\n")
        process_run(data["full_df1"], data["full_df2"], name1, name2, "Total Run")
        return
    intervals = summary_dict.get(run_name, [])

    if not intervals or len(intervals) < 2:
        print(f"Warning: Not enough interval data found for run '{run_name}'.\n")
        return

    # Upwind (interval 0)
    if onlyUpwind or (not onlyUpwind and not onlyDownwind):
        pp.pprint(intervals[0])
        if intervals[0]["duration"] < 30:
            print("\nSkipping Upwind interval: duration < 30 seconds.\n")
        else:
            start1 = datetime.utcfromtimestamp(intervals[0]["start_time"]).strftime("%Y-%m-%d %H:%M:%S")
            end1 = datetime.utcfromtimestamp(intervals[0]["end_time"]).strftime("%Y-%m-%d %H:%M:%S")
            title1 = f"Interval 1: Upwind from {start1} to {end1} — {name1} vs {name2}"
            process_run(data["reduced_boat1_int1_df"], data["reduced_boat2_int1_df"], name1, name2, title1)

    # Downwind (interval 1)
    if onlyDownwind or (not onlyUpwind and not onlyDownwind):
        print("-" * 40)
        print("Interval 2: Downwind")
        print("-" * 40)
        pp.pprint(intervals[1])
        if intervals[1]["duration"] < 30:
            print("\nSkipping Downwind interval: duration < 30 seconds.\n")
        else:
            start2 = datetime.utcfromtimestamp(intervals[1]["start_time"]).strftime("%Y-%m-%d %H:%M:%S")
            end2 = datetime.utcfromtimestamp(intervals[1]["end_time"]).strftime("%Y-%m-%d %H:%M:%S")
            title2 = f"Interval 2: Downwind from {start2} to {end2} — {name1} vs {name2}"
            print(f"\nProcessing: {title2}\n")
            process_run(data["reduced_boat1_int2_df"], data["reduced_boat2_int2_df"], name1, name2, title2)
"""
def process_all_run(run_path, summary_path, summary_results=None, tot=False, onlyUpwind=False, onlyDownwind=False):
    if summary_results is None:
        summary_results = []  # Initialize only if not passed in
    summary_dict = load_summary_intervals(summary_path)
    data = load_and_reduce_boat_data(run_path, summary_dict)
    name1, name2 = data["boat1_name"], data["boat2_name"]

    run_name = os.path.basename(run_path)
    print("\n\n\n\n" + "=" * 80)
    print(f"Processing run: {run_name}")
    print("=" * 80 + "\n")

    if tot:
        print("Processing total run (full data)...\n")
        gain, merged = process_run(data["full_df1"], data["full_df2"], name1, name2, "Total Run")
        row = extract_summary_row(run_name, name1, name2, gain, merged)
        summary_results.append(row)

    else:
        intervals = summary_dict.get(run_name, [])

        if not intervals or len(intervals) < 2:
            print(f"Warning: Not enough interval data found for run '{run_name}'.\n")
            return

        # Upwind (interval 0)
        if onlyUpwind or (not onlyUpwind and not onlyDownwind):
            pp.pprint(intervals[0])
            if intervals[0]["duration"] < 30:
                print("\nSkipping Upwind interval: duration < 30 seconds.\n")
            else:
                start1 = datetime.utcfromtimestamp(intervals[0]["start_time"]).strftime("%Y-%m-%d %H:%M:%S")
                end1 = datetime.utcfromtimestamp(intervals[0]["end_time"]).strftime("%Y-%m-%d %H:%M:%S")
                title1 = f"Interval 1: Upwind from {start1} to {end1} — {name1} vs {name2}"
                gain, merged = process_run(
                    data["reduced_boat1_int1_df"],
                    data["reduced_boat2_int1_df"],
                    name1, name2, title1
                )
                row = extract_summary_row(run_name + " (Upwind)", name1, name2, gain, merged)
                summary_results.append(row)

        # Downwind (interval 1)
        if onlyDownwind or (not onlyUpwind and not onlyDownwind):
            print("-" * 40)
            print("Interval 2: Downwind")
            print("-" * 40)
            pp.pprint(intervals[1])
            if intervals[1]["duration"] < 30:
                print("\nSkipping Downwind interval: duration < 30 seconds.\n")
            else:
                start2 = datetime.utcfromtimestamp(intervals[1]["start_time"]).strftime("%Y-%m-%d %H:%M:%S")
                end2 = datetime.utcfromtimestamp(intervals[1]["end_time"]).strftime("%Y-%m-%d %H:%M:%S")
                title2 = f"Interval 2: Downwind from {start2} to {end2} — {name1} vs {name2}"
                print(f"\nProcessing: {title2}\n")
                gain, merged = process_run(
                    data["reduced_boat1_int2_df"],
                    data["reduced_boat2_int2_df"],
                    name1, name2, title2
                )
                row = extract_summary_row(run_name + " (Downwind)", name1, name2, gain, merged)
                summary_results.append(row)

    # Display summary after all intervals
    if summary_results:
        df_summary = pd.DataFrame(summary_results)
    else:
        print("No valid runs to summarize.")

def extract_summary_row(run_name, name1, name2, gain_table, merged_stats):
    # Save original names for merged_stats lookup
    orig_name1 = name1
    orig_name2 = name2

    # Mapping logic to determine who is on SenseBoard
    name_map = {
        "SenseBoard": None,
        "Gian Stragiotti": "Karl Maeder*",
        "Karl Maeder": "Gian Stragiotti*"
    }

    # Determine display names
    display_name1 = name1
    display_name2 = name2

    if name1 == "SenseBoard":
        display_name1 = name_map.get(name2, "SenseBoard*")
    if name2 == "SenseBoard":
        display_name2 = name_map.get(name1, "SenseBoard*")

    master_name = display_name1
    slave_name = display_name2

    # --- Map winner names in merged_stats ---
    def map_winner_name(winner):
        if winner == "SenseBoard":
            if orig_name1 == "SenseBoard":
                return display_name1
            elif orig_name2 == "SenseBoard":
                return display_name2
        return winner  # unchanged if not SenseBoard

    winner_avg_sog = map_winner_name(merged_stats.at["SOG", "Winner (Avg)"])
    winner_std_sog = map_winner_name(merged_stats.at["SOG", "Winner (StdDev)"])
    winner_overall_sog = map_winner_name(merged_stats.at["SOG", "Winner (Overall)"])

    winner_avg_vmg = map_winner_name(merged_stats.at["VMG", "Winner (Avg)"])
    winner_std_vmg = map_winner_name(merged_stats.at["VMG", "Winner (StdDev)"])
    winner_overall_vmg = map_winner_name(merged_stats.at["VMG", "Winner (Overall)"])

    winner_avg_heel = map_winner_name(merged_stats.at["Heel_Lwd", "Winner (Avg)"])
    winner_std_heel = map_winner_name(merged_stats.at["Heel_Lwd", "Winner (StdDev)"])
    winner_overall_heel = map_winner_name(merged_stats.at["Heel_Lwd", "Winner (Overall)"])

    winner_avg_sideLines = map_winner_name(merged_stats.at["Side_lines", "Winner (Avg)"])
    winner_std_sideLines = map_winner_name(merged_stats.at["Side_lines", "Winner (StdDev)"])
    winner_overall_sideLines = map_winner_name(merged_stats.at["Side_lines", "Winner (Overall)"])

    winner_avg_lineC = map_winner_name(merged_stats.at["Line_C", "Winner (Avg)"])
    winner_std_lineC = map_winner_name(merged_stats.at["Line_C", "Winner (StdDev)"])
    winner_overall_lineC = map_winner_name(merged_stats.at["Line_C", "Winner (Overall)"])

    winner_avg_totalLines = map_winner_name(merged_stats.at["Total_lines", "Winner (Avg)"])
    winner_std_totalLines = map_winner_name(merged_stats.at["Total_lines", "Winner (StdDev)"])
    winner_overall_totalLines = map_winner_name(merged_stats.at["Total_lines", "Winner (Overall)"])
    
    row = {
            "Run": run_name,
            "Master": master_name,
            "Slave": slave_name,

            "Space1": "",  # séparateur visuel

            "Lateral Gain (m)": gain_table.at["Total Gain", "Lateral"],
            "Forward Gain (m)": gain_table.at["Total Gain", "Forward"],
            "VMG Gain (m)": gain_table.at["Total Gain", "VMG"],

            "Space2": "",
            "Avg SOG (Master)": merged_stats.at["SOG", f"Avg ({orig_name1})"],
            "Avg SOG (Slave)": merged_stats.at["SOG", f"Avg ({orig_name2})"],
            "Winner Avg SOG": winner_avg_sog,
            "Winner Std SOG": winner_std_sog,
            "Winner Overall SOG": winner_overall_sog,

            "Space3": "",
            "Avg VMG (Master)": merged_stats.at["VMG", f"Avg ({orig_name1})"],
            "Avg VMG (Slave)": merged_stats.at["VMG", f"Avg ({orig_name2})"],
            "Winner Avg VMG": winner_avg_vmg,
            "Winner Std VMG": winner_std_vmg,
            "Winner Overall VMG": winner_overall_vmg,

            "Space4": "",
            "Avg Heel (Master)": merged_stats.at["Heel_Lwd", f"Avg ({orig_name1})"],
            "Avg Heel (Slave)": merged_stats.at["Heel_Lwd", f"Avg ({orig_name2})"],
            "Winner Avg Heel": winner_avg_heel,
            "Winner Std Heel": winner_std_heel,
            "Winner Overall Heel": winner_overall_heel,

            "Space5": "",
            "Avg Side_Lines (Master)": merged_stats.at["Side_lines", f"Avg ({orig_name1})"],
            "Avg Side_Lines (Slave)": merged_stats.at["Side_lines", f"Avg ({orig_name2})"],
            "Winner Avg Side_Lines": winner_avg_sideLines,
            "Winner Std Side_Lines": winner_std_sideLines,
            "Winner Overall Side_Lines": winner_overall_sideLines,

            "Space6": "",
            "Avg Line_C (Master)": merged_stats.at["Line_C", f"Avg ({orig_name1})"],
            "Avg Line_C (Slave)": merged_stats.at["Line_C", f"Avg ({orig_name2})"],
            "Winner Avg Line_C": winner_avg_lineC,
            "Winner Std Line_C": winner_std_lineC,
            "Winner Overall Line_C": winner_overall_lineC,

            "Space7": "",
            "Avg Total_Lines (Master)": merged_stats.at["Total_lines", f"Avg ({orig_name1})"],
            "Avg Total_Lines (Slave)": merged_stats.at["Total_lines", f"Avg ({orig_name2})"],
            "Winner Avg Total_Lines": winner_avg_totalLines,
            "Winner Std Total_Lines": winner_std_totalLines,
            "Winner Overall Total_Lines": winner_overall_totalLines,



        }


    return row
