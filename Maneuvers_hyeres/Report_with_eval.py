import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from geopy.distance import geodesic
from IPython.display import display

"""
Script for analyzing and visualizing sailing maneuvers.

Main features:
- Load enriched data from a CSV file (positions, speeds, angles, forces, etc.).
- Evaluate each maneuver using several metrics:
    1. Ratio between the actual path distance and the straight-line distance (Path/AB).
    2. Distance lost in terms of Speed Over Ground (SOG).
    3. Distance lost in terms of Velocity Made Good (VMG).
- Print numerical summaries for each maneuver.
- Generate detailed plots (SOG, COG, VMG, angles, forces, etc.) with moving average smoothing.
- Produce a final summary table of evaluations, sorted by Path/AB ratio.

Configurable parameters:
- FICHIER_CSV : path to the enriched CSV file containing the data.
- MA_WINDOW   : window size for moving average applied to time series.

Usage:
- Call `plot(df, rider_name, maneuver_type_filter=None)` to analyze a given rider,
  with an optional filter for maneuver type.
"""

# === PARAMETERS ===
FICHIER_CSV = "all_data_enriched.csv"
MA_WINDOW = 10  # moving average window size

# === LOAD DATA ===
df = pd.read_csv(FICHIER_CSV, low_memory=False)

# === Evaluation Functions ===
def compute_path_distance(latitudes, longitudes):
    points = list(zip(latitudes, longitudes))
    return sum(geodesic(points[i], points[i+1]).meters for i in range(len(points)-1))

def compute_straight_line_distance(lat1, lon1, lat2, lon2):
    return geodesic((lat1, lon1), (lat2, lon2)).meters

def compute_integral(time, speed):
    return np.trapz(speed, time)

def evaluate_maneuver(maneuver_data):
    times = maneuver_data['SecondsSince1970'].values
    sog = maneuver_data['SOG'].values
    vmg = maneuver_data['VMG'].values

    # Eval 1
    path_distance = compute_path_distance(maneuver_data['Lat'].values, maneuver_data['Lon'].values)
    A_lat, A_lon = maneuver_data['Lat'].iloc[0], maneuver_data['Lon'].iloc[0]
    B_lat, B_lon = maneuver_data['Lat'].iloc[-1], maneuver_data['Lon'].iloc[-1]
    ab_distance = compute_straight_line_distance(A_lat, A_lon, B_lat, B_lon)
    ratio_path_ab = path_distance / ab_distance if ab_distance != 0 else np.nan

    # Eval 2
    dt = times[-1] - times[0]
    v_avg_entry = np.mean(sog[:10])
    dx_sog = v_avg_entry * dt
    integral_sog = compute_integral(times, sog)
    distance_lost_sog = dx_sog - integral_sog

    # Eval 3
    v_avg_entry_vmg = np.mean(vmg[:10])
    dx_vmg = v_avg_entry_vmg * dt
    integral_vmg = compute_integral(times, vmg)
    distance_lost_vmg = dx_vmg - integral_vmg

    return {
        "Ratio Path/AB": ratio_path_ab,
        "Distance Lost (SOG)": distance_lost_sog,
        "Distance Lost (VMG)": distance_lost_vmg
    }

def plot(df, rider_name, maneuver_type_filter=None):
    rider_data = df[df['rider_name'] == rider_name]
    if rider_data.empty:
        print(f"No data found for rider: {rider_name}")
        return

    eval_records = []

    for run_name in rider_data['run'].unique():
        run_data = rider_data[rider_data['run'] == run_name]

        for maneuver_index in run_data['maneuver_index'].unique():
            maneuver_data = run_data[run_data['maneuver_index'] == maneuver_index]
            maneuver_type = maneuver_data['maneuver_type'].iloc[0]

            if maneuver_type_filter and maneuver_type != maneuver_type_filter:
                continue

            # Evaluation
            eval_results = evaluate_maneuver(maneuver_data)

            # Save eval data
            eval_records.append({
                "Run": run_name,
                "Maneuver ID": maneuver_index,
                "Eval 1 - Ratio Path/AB": eval_results['Ratio Path/AB'],
                "Eval 2 - Distance Lost (SOG)": eval_results['Distance Lost (SOG)'],
                "Eval 3 - Distance Lost (VMG)": eval_results['Distance Lost (VMG)']
            })

            # Console summary
            print(f"\n=== {rider_name} - Run: {run_name} - Maneuver {maneuver_index} ({maneuver_type}) ===")
            print(f"Start: {maneuver_data['start_time'].iloc[0]} | End: {maneuver_data['end_time'].iloc[0]}")
            print(f"Duration: {maneuver_data['interval_duration'].iloc[0]} sec")
            print(f"TWS mean: {maneuver_data['TWS'].mean():.2f} kn | TWA mean: {maneuver_data['TWA'].mean():.2f}° | TWD mean: {maneuver_data['TWD'].mean():.2f}°")
            print(f"[Eval 1] Path / AB Ratio       : {eval_results['Ratio Path/AB']:.3f}")
            print(f"[Eval 2] Distance Lost (SOG)   : {eval_results['Distance Lost (SOG)']:.2f} m")
            print(f"[Eval 3] Distance Lost (VMG)   : {eval_results['Distance Lost (VMG)']:.2f} m")

            # === PLOTTING PART (unchanged, so kept intact) ===
            fig, axes = plt.subplots(3, 5, figsize=(20, 12))
            fig.suptitle(f'{rider_name} - Run: {run_name} - Maneuver ID: {maneuver_index} - Maneuver type: {maneuver_type}', fontsize=16)

            # Lat/Lon (no moving average)
            axes[0, 0].plot(maneuver_data['Lon'], maneuver_data['Lat'], color='blue')
            axes[0, 0].set_title("Lat (y) / Lon (x)")
            axes[0, 0].set_xlabel("Longitude")
            axes[0, 0].set_ylabel("Latitude")

            # SOG
            axes[0, 1].plot(maneuver_data['SecondsSince1970'], maneuver_data['SOG'], color='green', alpha=0.5)
            axes[0, 1].plot(maneuver_data['SecondsSince1970'], maneuver_data['SOG'].rolling(MA_WINDOW, min_periods=1, center=True).mean(), color='black')
            axes[0, 1].set_title("Speed Over Ground (SOG)")
            axes[0, 1].set_xlabel("Time")
            axes[0, 1].set_ylabel("SOG (knots)")
            axes[0, 1].tick_params(axis='x', rotation=45)

            # COG
            axes[0, 2].plot(maneuver_data['SecondsSince1970'], maneuver_data['COG'], color='orange', alpha=0.5)
            axes[0, 2].plot(maneuver_data['SecondsSince1970'], maneuver_data['COG'].rolling(MA_WINDOW, min_periods=1, center=True).mean(), color='black')
            axes[0, 2].set_title("Course Over Ground (COG)")
            axes[0, 2].set_xlabel("Time")
            axes[0, 2].set_ylabel("COG (degrees)")
            axes[0, 2].tick_params(axis='x', rotation=45)

            # Heel_Abs
            axes[0, 3].plot(maneuver_data['SecondsSince1970'], maneuver_data['Heel_Abs'], color='red', alpha=0.5)
            axes[0, 3].plot(maneuver_data['SecondsSince1970'], maneuver_data['Heel_Abs'].rolling(MA_WINDOW, min_periods=1, center=True).mean(), color='black')
            axes[0, 3].set_title("Heel_Abs Angle")
            axes[0, 3].set_xlabel("Time")
            axes[0, 3].set_ylabel("Heel_Abs (degrees)")
            axes[0, 3].tick_params(axis='x', rotation=45)

            # Trim
            axes[0, 4].plot(maneuver_data['SecondsSince1970'], maneuver_data['Trim'], color='red', alpha=0.5)
            axes[0, 4].plot(maneuver_data['SecondsSince1970'], maneuver_data['Trim'].rolling(MA_WINDOW, min_periods=1, center=True).mean(), color='black')
            axes[0, 4].set_title("Trim Angle")
            axes[0, 4].set_xlabel("Time")
            axes[0, 4].set_ylabel("Trim (degrees)")
            axes[0, 4].tick_params(axis='x', rotation=45)

            # Side_line2
            axes[1, 0].plot(maneuver_data['SecondsSince1970'], maneuver_data['side_line2'], color='cyan', alpha=0.5)
            axes[1, 0].plot(maneuver_data['SecondsSince1970'], maneuver_data['side_line2'].rolling(MA_WINDOW, min_periods=1, center=True).mean(), color='black')
            axes[1, 0].set_title("Side_lines2")
            axes[1, 0].set_xlabel("Time")
            axes[1, 0].set_ylabel("Side_lines2 (units)")
            axes[1, 0].tick_params(axis='x', rotation=45)

            # Line_C2
            axes[1, 1].plot(maneuver_data['SecondsSince1970'], maneuver_data['Line_C2'], color='blue', alpha=0.5)
            axes[1, 1].plot(maneuver_data['SecondsSince1970'], maneuver_data['Line_C2'].rolling(MA_WINDOW, min_periods=1, center=True).mean(), color='black')
            axes[1, 1].set_title("Central Line")
            axes[1, 1].set_xlabel("Time")
            axes[1, 1].set_ylabel("Force (N)")
            axes[1, 1].tick_params(axis='x', rotation=45)

            # VMG
            axes[1, 2].plot(maneuver_data['SecondsSince1970'], maneuver_data['VMG'], color='gray', alpha=0.5)
            axes[1, 2].plot(maneuver_data['SecondsSince1970'], maneuver_data['VMG'].rolling(MA_WINDOW, min_periods=1, center=True).mean(), color='black')
            axes[1, 2].set_title("VMG")
            axes[1, 2].set_xlabel("Time")
            axes[1, 2].set_ylabel("VMG (m/s)")
            axes[1, 2].tick_params(axis='x', rotation=45)

            if (maneuver_data['boat_name'] == "SenseBoard").all():
                # F_back
                axes[1, 3].plot(maneuver_data['SecondsSince1970'], maneuver_data['F_back'], color='blue', alpha=0.5)
                axes[1, 3].plot(maneuver_data['SecondsSince1970'], maneuver_data['F_back'].rolling(MA_WINDOW, min_periods=1, center=True).mean(), color='black')
                axes[1, 3].set_title("Back Force (F_back)")
                axes[1, 3].set_xlabel("Time")
                axes[1, 3].set_ylabel("Force (N)")
                axes[1, 3].tick_params(axis='x', rotation=45)

                # F_front
                axes[1, 4].plot(maneuver_data['SecondsSince1970'], maneuver_data['F_front'], color='green', alpha=0.5)
                axes[1, 4].plot(maneuver_data['SecondsSince1970'], maneuver_data['F_front'].rolling(MA_WINDOW, min_periods=1, center=True).mean(), color='black')
                axes[1, 4].set_title("Front Force (F_front)")
                axes[1, 4].set_xlabel("Time")
                axes[1, 4].set_ylabel("Force (N)")
                axes[1, 4].tick_params(axis='x', rotation=45)

            # Hide empty subplots
            axes[2, 0].axis('off')
            axes[2, 1].axis('off')
            axes[2, 2].axis('off')
            axes[2, 3].axis('off')
            axes[2, 4].axis('off')

            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            plt.show()

    # Create DataFrame and sort by Eval 1
    eval_df = pd.DataFrame(eval_records)
    eval_df_sorted = eval_df.sort_values(by="Eval 1 - Ratio Path/AB", ascending=True)

    # Display final evaluation table
    print(f"\n=== Evaluation Summary for {rider_name} doing '{maneuver_type_filter or 'all types'}' maneuvers — Sorted by Eval 1 (Ratio Path/AB) ===")
    pd.set_option('display.max_rows', None)
    display(eval_df_sorted)  # For Jupyter. Use print(eval_df_sorted) otherwise
