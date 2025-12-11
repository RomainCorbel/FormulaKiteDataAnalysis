import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def extract_boat_name(file_path: str) -> str:
    """
    Extract boat name from CSV file name (without extension)
    """
    return os.path.splitext(os.path.basename(file_path))[0]

def detect_COG_changes_rolling_mean(df: pd.DataFrame, value_col: str = 'COG',
                                    threshold: float = 15.0, window: int = 20) -> pd.DataFrame:
    """
    Detect changes in COG by comparing rolling means before and after each point.
    """
    cog = df[value_col].copy()
    n = len(cog)

    diffs = []
    for i in range(window, n - window):
        before = cog[i - window:i]
        after = cog[i + 1:i + 1 + window]
        
        mean_before = np.mean(before)
        mean_after = np.mean(after)

        # Handle circular difference
        delta = np.abs(mean_after - mean_before)
        delta = min(delta, 360 - delta)
        diffs.append(delta)
    diffs = np.array(diffs)

    change_indices = np.where(diffs > threshold)[0] + window  # shift due to slicing

    return df.loc[change_indices, ['Lat', 'Lon', value_col, 'SecondsSince1970']].assign(index=change_indices)

def plot_full_trajectories(
    boat1_df,
    boat2_df,
    boat1_changes,
    boat2_changes,
    boat1_name="boat1",
    boat2_name="boat2",
    show_changes=True
):
    """
    Plot full trajectories of both boats.
    Optionally overlay COG change points if show_changes is True.
    """
    colors = {boat1_name: 'green', boat2_name: 'blue'}

    plt.figure(figsize=(10, 8))

    # Trajectoires des bateaux
    plt.scatter(boat2_df['Lon'], boat2_df['Lat'], c=colors[boat2_name], marker='x', s=10, label=f'Trajectory {boat2_name}')
    plt.scatter(boat1_df['Lon'], boat1_df['Lat'], c=colors[boat1_name], marker='x', s=10, label=f'Trajectory {boat1_name}')

    # Points de changement de cap si demandé
    if show_changes:
        plt.scatter(boat2_changes['Lon'], boat2_changes['Lat'], c='red', s=40, label='COG Change Points')
        plt.scatter(boat1_changes['Lon'], boat1_changes['Lat'], c='red', s=40)

    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Trajectories' + (' with COG Change Points' if show_changes else ''))
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def compute_longest_intervals(
    boat1_changes: pd.DataFrame,
    boat2_changes: pd.DataFrame,
    boat1_df: pd.DataFrame,
    boat2_df: pd.DataFrame,
    top_n: int = 2,
    boat1_name: str = "boat1",
    boat2_name: str = "boat2",
    min_duration_sec: float = 30.0,
    sog_derivative_threshold: float = 0.2,
    smoothing_window: int = 300
) -> list[dict]:
    
    # Mark source of change points
    boat1_changes['source'] = boat1_name
    boat2_changes['source'] = boat2_name
    
    # Combine and sort all change points chronologically
    all_changes = pd.concat([boat1_changes, boat2_changes], ignore_index=True)
    all_changes_sorted = all_changes.sort_values('SecondsSince1970').reset_index(drop=True)
    
    # Preprocess SOG data with smoothing and derivative calculation
    for df in [boat1_df, boat2_df]:
        # Smooth SOG data to reduce noise
        df['SOG_smoothed'] = df['SOG'].rolling(
            window=smoothing_window,
            min_periods=1,
            center=True
        ).mean()
        
        # Calculate robust derivative using central differences
        df['SOG_derivative'] = (
            df['SOG_smoothed'].diff(2) / 
            df['SecondsSince1970'].diff(2).abs()
        ).abs()
    intervals = []
    
    for i in range(len(all_changes_sorted) - 1):
        start = all_changes_sorted.loc[i, 'SecondsSince1970']
        end = all_changes_sorted.loc[i + 1, 'SecondsSince1970']
        
        # Get data for this interval
        boat1_interval = boat1_df[(boat1_df['SecondsSince1970'] >= start) & 
                                (boat1_df['SecondsSince1970'] <= end)].copy()
        boat2_interval = boat2_df[(boat2_df['SecondsSince1970'] >= start) & 
                                (boat2_df['SecondsSince1970'] <= end)].copy()
        
        if boat1_interval.empty or boat2_interval.empty:
            continue
            
        # Merge the two boats' data by time
        merged = pd.merge_asof(
            boat1_interval.sort_values('SecondsSince1970'),
            boat2_interval.sort_values('SecondsSince1970'),
            on='SecondsSince1970',
            suffixes=('_boat1', '_boat2')
        )
        
        # Find periods where both boats have stable speed
        stable_mask = (
            (merged['SOG_derivative_boat1'] < sog_derivative_threshold) &
            (merged['SOG_derivative_boat2'] < sog_derivative_threshold))
        
        # Group consecutive stable periods
        stable_groups = (stable_mask != stable_mask.shift(1)).cumsum()
        
        for group_id, group_data in merged[stable_mask].groupby(stable_groups):
            group_start = group_data['SecondsSince1970'].min()
            group_end = group_data['SecondsSince1970'].max()
            group_duration = group_end - group_start
            
            if group_duration >= min_duration_sec:
                # Calculate additional metrics
                avg_sog1 = group_data['SOG_boat1'].mean()
                avg_sog2 = group_data['SOG_boat2'].mean()
                
                intervals.append({
                    'start_time': group_start,
                    'end_time': group_end,
                    'duration': group_duration,
                    'boat1_name': boat1_name,
                    'boat2_name': boat2_name,
                    'avg_SOG_boat1': avg_sog1,
                    'avg_SOG_boat2': avg_sog2,
                    'SOG_variation_boat1': group_data['SOG_boat1'].std(),
                    'SOG_variation_boat2': group_data['SOG_boat2'].std(),
                    'stability_score': 1/(1 + group_data[['SOG_derivative_boat1', 
                                                       'SOG_derivative_boat2']].mean().mean())
                })
    
    # Sort by duration and stability score
    return sorted(intervals, 
                 key=lambda x: (-x['duration'], -x['stability_score']))[:top_n]

import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec

def plot_sog_with_intervals(
    boat1_df: pd.DataFrame,
    boat2_df: pd.DataFrame,
    intervals: list[dict],
    boat1_name: str = "boat1",
    boat2_name: str = "boat2"
):
    """
    Plot raw and smoothed SOG for both boats with vertical lines indicating stable intervals.
    """
    plt.figure(figsize=(15, 8))
    
    time_offset = boat1_df['SecondsSince1970'].min()
    time1 = boat1_df['SecondsSince1970'] - time_offset
    time2 = boat2_df['SecondsSince1970'] - time_offset

    # --- Plot raw and smoothed SOG ---
    plt.plot(time1, boat1_df['SOG'], color='green', alpha=0.3, label=f'{boat1_name} Raw SOG')
    plt.plot(time1, boat1_df['SOG_smoothed'], color='green', linewidth=1.5, label=f'{boat1_name} Smoothed SOG')

    plt.plot(time2, boat2_df['SOG'], color='blue', alpha=0.3, label=f'{boat2_name} Raw SOG')
    plt.plot(time2, boat2_df['SOG_smoothed'], color='blue', linewidth=1.5, label=f'{boat2_name} Smoothed SOG')

    # --- Vertical lines for flat/stable intervals ---
    for i, interval in enumerate(intervals, 1):
        start = interval['start_time'] - time_offset
        end = interval['end_time'] - time_offset
        plt.axvline(start, color='red', linestyle='--', linewidth=1)
        plt.axvline(end, color='red', linestyle='--', linewidth=1)
        plt.text((start + end) / 2, plt.ylim()[1]*0.95, f"#{i}", color='red',
                 ha='center', va='top', fontsize=9, fontweight='bold', rotation=0)

    plt.xlabel('Time (seconds from start)')
    plt.ylabel('SOG (knots)')
    plt.title('SOG with Smoothed Curve and Stable Intervals')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()



def add_avg_twa_to_intervals(intervals: list[dict], boat1_df: pd.DataFrame, boat2_df: pd.DataFrame) -> list[dict]:
    """
    Pour chaque intervalle, ajoute la moyenne de TWA pour chaque bateau séparément.
    """
    for interval in intervals:
        start = interval['start_time']
        end = interval['end_time']

        # Moyenne TWA pour boat1
        mask1 = (boat1_df['SecondsSince1970'] >= start) & (boat1_df['SecondsSince1970'] <= end)
        twa_values1 = boat1_df.loc[mask1, 'TWA']
        interval['avg TWA boat1'] = twa_values1.mean() if not twa_values1.empty else None

        # Moyenne TWA pour boat2
        mask2 = (boat2_df['SecondsSince1970'] >= start) & (boat2_df['SecondsSince1970'] <= end)
        twa_values2 = boat2_df.loc[mask2, 'TWA']
        interval['avg TWA boat2'] = twa_values2.mean() if not twa_values2.empty else None

    return intervals

def load_boat_data(boat1_path: str, boat2_path: str) -> tuple[pd.DataFrame, pd.DataFrame, str, str]:
    """
    Load boat data from CSV files and extract boat names.
    Returns dataframes and corresponding boat names.
    """
    boat1_df = pd.read_csv(boat1_path)
    boat2_df = pd.read_csv(boat2_path)

    boat1_name = extract_boat_name(boat1_path)
    boat2_name = extract_boat_name(boat2_path)

    return boat1_df, boat2_df, boat1_name, boat2_name

def analyze_session(boat1_path: str, boat2_path: str) -> list[dict]:
    """
    Perform a full analysis of a sailing session given CSV paths for boat1 and boat2.
    Returns a list of the top N longest intervals with avg TWA per boat.
    """
    # Load data
    boat1_df, boat2_df, boat1_name, boat2_name = load_boat_data(boat1_path, boat2_path)

    # Detect COG change points
    boat1_changes = detect_COG_changes_rolling_mean(boat1_df)
    boat2_changes = detect_COG_changes_rolling_mean(boat2_df)

    # Plot full trajectories with COG changes
    plot_full_trajectories(boat1_df, boat2_df, boat1_changes, boat2_changes, boat1_name, boat2_name)

    # Compute longest intervals between change points
    longest_intervals = compute_longest_intervals(
        boat1_changes, boat2_changes,
        boat1_df, boat2_df,
        top_n=2,
        boat1_name=boat1_name,
        boat2_name=boat2_name
    )
    
    # Add average TWA per boat
    longest_intervals = add_avg_twa_to_intervals(longest_intervals, boat1_df, boat2_df)

    # Sort intervals chronologically for display and export
    longest_intervals = sorted(longest_intervals, key=lambda x: x['start_time'])

    # Plot the longest trajectory segments
    # plot_longest_segments(boat1_df, boat2_df, longest_intervals, boat1_name, boat2_name)
    plot_sog_with_intervals(boat1_df, boat2_df, longest_intervals, boat1_name, boat2_name)

    return longest_intervals