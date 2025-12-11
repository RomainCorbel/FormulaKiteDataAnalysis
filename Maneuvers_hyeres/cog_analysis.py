import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import scipy.signal
from scipy.signal import find_peaks

def extract_boat_name(file_path: str) -> str:
    """
    Extract boat name from CSV file name (without extension)
    """
    return os.path.splitext(os.path.basename(file_path))[0]

def detect_COG_changes_rolling_mean(df: pd.DataFrame, value_col: str = 'COG',
                                    threshold: float = 30.0, window: int = 30) -> pd.DataFrame:
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

def plot_trajectories(
    boat1_df: pd.DataFrame,
    boat1_changes: pd.DataFrame,
    boat2_df: pd.DataFrame = None,
    boat2_changes: pd.DataFrame = None,
    boat1_name: str = "boat1",
    boat2_name: str = "boat2",
    show_changes: bool = True,
    boat1_sog_maneuvers: list[dict] = None,
    boat2_sog_maneuvers: list[dict] = None
):
    """
    Plot trajectories of one or two boats, showing:
    - Trajectory path
    - COG change points
    - SOG maneuver segments
    - Local SOG minima with numbered labels
    """
    plt.figure(figsize=(10, 8))
    colors = {boat1_name: 'green', boat2_name: 'blue'}

    # --- Boat 1 trajectory ---
    plt.scatter(boat1_df['Lon'], boat1_df['Lat'], c=colors[boat1_name], marker='x', s=10, label=f'Trajectory {boat1_name}')

    # --- Boat 1 COG changes ---
    if show_changes and boat1_changes is not None:
        plt.scatter(boat1_changes['Lon'], boat1_changes['Lat'], c='red', s=70, label=f'{boat1_name} COG Changes')

    # --- Boat 1 SOG maneuvers ---
    if boat1_sog_maneuvers:
        sog_points = pd.DataFrame()
        sog_min_points = []
        maneuver_labels = {}  # key = maneuver_time, value = index to display

        # Récupère les manœuvres numérotées (matching COG)
        maneuver_labels, _ = get_valid_maneuvers_with_cog(boat1_sog_maneuvers, boat1_changes)

        for m in boat1_sog_maneuvers:
            segment = boat1_df[
                (boat1_df['SecondsSince1970'] >= m['start_time']) &
                (boat1_df['SecondsSince1970'] <= m['end_time'])
            ]
            sog_points = pd.concat([sog_points, segment], ignore_index=True)

            min_idx = boat1_df['SecondsSince1970'].sub(m['maneuver_time']).abs().idxmin()
            min_point = boat1_df.loc[min_idx]
            sog_min_points.append((m, min_point))

        # Affichage des segments SOG
        if not sog_points.empty:
            plt.scatter(sog_points['Lon'], sog_points['Lat'], c='purple', s=20, label=f'{boat1_name} SOG Maneuvers')

        # Minima locaux avec ou sans numéro
        for m, point in sog_min_points:
            plt.scatter(point['Lon'], point['Lat'], color='yellow', marker='x', s=60)
            if m['maneuver_time'] in maneuver_labels:
                idx = maneuver_labels[m['maneuver_time']]
                plt.text(point['Lon']+0.00003, point['Lat'], f"#{idx}", color='blue', fontsize=11)

    # --- Boat 2 trajectory ---
    if boat2_df is not None:
        plt.scatter(boat2_df['Lon'], boat2_df['Lat'], c=colors[boat2_name], marker='x', s=10, label=f'Trajectory {boat2_name}')

        if show_changes and boat2_changes is not None:
            plt.scatter(boat2_changes['Lon'], boat2_changes['Lat'], c='orange', s=40, label=f'{boat2_name} COG Changes')

        if boat2_sog_maneuvers:
            sog_points = pd.DataFrame()
            sog_min_points = []

            for i, m in enumerate(boat2_sog_maneuvers, start=1):
                segment = boat2_df[
                    (boat2_df['SecondsSince1970'] >= m['start_time']) &
                    (boat2_df['SecondsSince1970'] <= m['end_time'])
                ]
                sog_points = pd.concat([sog_points, segment], ignore_index=True)

                min_idx = boat2_df['SecondsSince1970'].sub(m['maneuver_time']).abs().idxmin()
                min_point = boat2_df.loc[min_idx]
                sog_min_points.append((i, min_point))

            if not sog_points.empty:
                plt.scatter(sog_points['Lon'], sog_points['Lat'], c='magenta', s=30, label=f'{boat2_name} SOG Maneuvers')

            if sog_min_points:
                for i, point in sog_min_points:
                    plt.scatter(point['Lon'], point['Lat'], color='black', marker='x', s=60, label='local SOG min,imum')
                    plt.text(point['Lon'] + 0.0003, point['Lat'] + 0.0003, f"#{i}", color='black', fontsize=9)

    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Trajectory with COG Changes and SOG Maneuvers')
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

    # Mono-bateau
    if boat2_changes is None or boat2_df is None:
        boat1_df['SOG_smoothed'] = boat1_df['SOG'].rolling(window=smoothing_window, min_periods=1, center=True).mean()
        boat1_df['SOG_derivative'] = boat1_df['SOG_smoothed'].diff(2).abs() / boat1_df['SecondsSince1970'].diff(2).abs()
        
        intervals = []
        changes = boat1_changes.sort_values('SecondsSince1970')
        for i in range(len(changes) - 1):
            start = changes.iloc[i]['SecondsSince1970']
            end = changes.iloc[i + 1]['SecondsSince1970']
            segment = boat1_df[(boat1_df['SecondsSince1970'] >= start) & (boat1_df['SecondsSince1970'] <= end)]
            if segment.empty:
                continue

            stable = segment[segment['SOG_derivative'] < sog_derivative_threshold]
            if stable.empty:
                continue

            duration = stable['SecondsSince1970'].max() - stable['SecondsSince1970'].min()
            if duration >= min_duration_sec:
                intervals.append({
                    'start_time': stable['SecondsSince1970'].min(),
                    'end_time': stable['SecondsSince1970'].max(),
                    'duration': duration,
                    'avg_SOG': stable['SOG'].mean(),
                    'SOG_variation': stable['SOG'].std(),
                    'stability_score': 1 / (1 + stable['SOG_derivative'].mean()),
                    'boat_name': boat1_name
                })

        return sorted(intervals, key=lambda x: (-x['duration'], -x['stability_score']))[:top_n]

    # Deux bateaux (version originale inchangée)
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

def plot_sog_with_intervals(boat1_df, boat2_df, intervals, boat1_name="boat1", boat2_name="boat2"):
    plt.figure(figsize=(15, 8))
    offset = boat1_df['SecondsSince1970'].min()
    time1 = boat1_df['SecondsSince1970'] - offset
    plt.plot(time1, boat1_df['SOG'], alpha=0.3, label=f'{boat1_name} Raw SOG')
    plt.plot(time1, boat1_df.get('SOG_smoothed', boat1_df['SOG']), label=f'{boat1_name} Smoothed SOG')

    if 'maneuver_time' in intervals[0]:
        min_sog_times = [interval['maneuver_time'] - offset for interval in intervals]
        min_sog_values = [interval['min_SOG'] for interval in intervals]
        plt.plot(min_sog_times, min_sog_values, 'o--', color='orange', label=f'{boat1_name} Min SOG')

    if boat2_df is not None:
        time2 = boat2_df['SecondsSince1970'] - offset
        plt.plot(time2, boat2_df['SOG'], alpha=0.3, label=f'{boat2_name} Raw SOG')
        plt.plot(time2, boat2_df.get('SOG_smoothed', boat2_df['SOG']), label=f'{boat2_name} Smoothed SOG')

    for i, interval in enumerate(intervals, 1):
        start = interval['start_time'] - offset
        end = interval['end_time'] - offset
        plt.axvline(start, color='red', linestyle='--')
        plt.axvline(end, color='red', linestyle='--')
        plt.text((start + end)/2, plt.ylim()[1]*0.95, f"#{i}", ha='center', color='red')

    plt.xlabel("Time (s)")
    plt.ylabel("SOG (knots)")
    plt.title("SOG and Stable Intervals")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


    if boat2_df is not None:
        time2 = boat2_df['SecondsSince1970'] - offset
        plt.plot(time2, boat2_df['SOG'], alpha=0.3, label=f'{boat2_name} Raw SOG')
        plt.plot(time2, boat2_df.get('SOG_smoothed', boat2_df['SOG']), label=f'{boat2_name} Smoothed SOG')
        for i, interval in enumerate(intervals, 1):
            start = interval['start_time'] - offset
            end = interval['end_time'] - offset
            plt.axvline(start, color='red', linestyle='--')
            plt.axvline(end, color='red', linestyle='--')
            plt.text((start + end)/2, plt.ylim()[1]*0.95, f"#{i}", ha='center', color='red')

        plt.xlabel("Time (s)")
        plt.ylabel("SOG (knots)")
        plt.title("SOG and Stable Intervals")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

def add_avg_twa_to_intervals(intervals: list[dict], boat1_df: pd.DataFrame, boat2_df: pd.DataFrame = None) -> list[dict]:
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

        # Moyenne TWA pour boat2 si disponible
        if boat2_df is not None:
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


def analyze_session(
    boat1_path: str, boat2_path: str = None, 
    cog_threshold: float = 30.0, window: int = 30, 
    sog_smoothing_window: int = 100, sog_prominence: float = 0.3, 
    sog_min_duration: float = 5.0, twa_threshold: float = 90.0, 
    cog_inversion_threshold: float = 45.0, min_minima_distance: float = 5.0, 
    top_n_intervals: int = 2, min_duration_sec: float = 30.0, 
    sog_derivative_threshold: float = 0.2, smoothing_window: int = 300,
    pre_window: float = 10.0, post_window: float = 5.0, min_sog_entry_threshold: float = 18.0
) -> list[dict]:

    boat1_df = pd.read_csv(boat1_path)
    boat1_name = extract_boat_name(boat1_path)

    if boat2_path is None:
        # --- Mono-bateau ---
        # Étapes : COG → SOG → Fusion logique
        boat1_changes = detect_COG_changes_rolling_mean(boat1_df, value_col='COG', threshold=cog_threshold, window=window)
        maneuvers = detect_maneuvers_from_sog_minima(
            boat1_df, 
            smoothing_window=sog_smoothing_window, 
            prominence=sog_prominence, 
            min_duration=sog_min_duration, 
            twa_threshold=twa_threshold, 
            cog_inversion_threshold=cog_inversion_threshold, 
            min_minima_distance=min_minima_distance,pre_window=pre_window, 
            post_window=post_window, min_sog_entry_threshold=min_sog_entry_threshold)


        # Identifier les manœuvres pertinentes (SOG + COG)
        valid_maneuver_map, summary = get_valid_maneuvers_with_cog(maneuvers, boat1_changes)

        # Plot avec toutes les manœuvres SOG, mais seules les valides ont un numéro
        plot_trajectories(
            boat1_df,
            boat1_changes,
            boat1_name=boat1_name,
            boat1_sog_maneuvers=maneuvers  # on passe tout
        )

        if summary:
            # Affichage SOG zoomé sur les segments valides
            plot_sog_with_intervals(boat1_df, None, [m for m in maneuvers if m['maneuver_time'] in valid_maneuver_map], boat1_name)
            return summary
        else:
            print("⚠️ Aucune manœuvre SOG détectée proche d’un changement de COG.")
            return []

    else:
        # --- Deux bateaux : logique inchangée ---
        boat2_df = pd.read_csv(boat2_path)
        boat2_name = extract_boat_name(boat2_path)

        boat1_changes = detect_COG_changes_rolling_mean(boat1_df, value_col='COG', threshold=cog_threshold, window=window)
        boat2_changes = detect_COG_changes_rolling_mean(boat2_df, value_col='COG', threshold=cog_threshold, window=window)

        plot_trajectories(
            boat1_df, boat1_changes,
            boat2_df=boat2_df, boat2_changes=boat2_changes,
            boat1_name=boat1_name, boat2_name=boat2_name
        )

        intervals = compute_longest_intervals(
            boat1_changes, boat2_changes,
            boat1_df, boat2_df,
            top_n=top_n_intervals,
            boat1_name=boat1_name,
            boat2_name=boat2_name,
            min_duration_sec=min_duration_sec,
            sog_derivative_threshold=sog_derivative_threshold,
            smoothing_window=smoothing_window
        )

        add_avg_twa_to_intervals(intervals, boat1_df, boat2_df)
        plot_sog_with_intervals(boat1_df, boat2_df, intervals, boat1_name, boat2_name)

        return intervals


def merge_maneuvers_and_cog_changes(
    maneuvers: list[dict],
    cog_changes: pd.DataFrame
) -> list[dict]:
    matched = []
    for m in maneuvers:
        start = m['start_time']
        end = m['end_time']

        # Filtrer les changements COG dans la fenêtre de manœuvre
        within_window = cog_changes[
            (cog_changes['SecondsSince1970'] >= start) &
            (cog_changes['SecondsSince1970'] <= end)
        ]

        if not within_window.empty:
            # Associer le point COG le plus proche du min SOG
            m_time = m['maneuver_time']
            closest_cog = within_window.iloc[
                (within_window['SecondsSince1970'] - m_time).abs().argmin()
            ]

            # Ajouter des infos du changement COG à la manœuvre
            m['COG_change_time'] = closest_cog['SecondsSince1970']
            m['COG_change_Lon'] = closest_cog['Lon']
            m['COG_change_Lat'] = closest_cog['Lat']

            matched.append(m)

    return matched

def get_valid_maneuvers_with_cog(
    maneuvers: list[dict],
    cog_changes: pd.DataFrame
) -> tuple[list[dict], dict]:
    valid_maneuvers = {}
    summary = []
    counter = 1

    for m in maneuvers:
        start, end = m['start_time'], m['end_time']
        m_time = m['maneuver_time']

        matches = cog_changes[
            (cog_changes['SecondsSince1970'] >= start) &
            (cog_changes['SecondsSince1970'] <= end)
        ]

        if not matches.empty:
            valid_maneuvers[m_time] = counter
            summary.append({
                'maneuver_index': counter,
                'maneuver_time': m_time,
                'maneuver_type': m['maneuver_type'],
                'duration': m['duration'],
                'start_time': start,
                'end_time': end
            })
            counter += 1

    return valid_maneuvers, summary

def detect_maneuvers_from_sog_minima(
    boat_df: pd.DataFrame,
    smoothing_window: int = 100,
    prominence: float = 0.3,
    min_duration: float = 5.0,
    twa_threshold: float = 90.0,
    cog_inversion_threshold: float = 45.0,  # Seuil de changement de cap significatif
    min_minima_distance: float = 5.0,       # Minimum time difference (in seconds) between two minima
    pre_window: float = 8.0,                # Temps avant le minimum SOG pour définir la manœuvre
    post_window: float = 3.0,                # Temps après le minimum SOG pour définir la manœuvre
    min_sog_entry_threshold: float = 18.0  # New: Minimum entry speed in knots
) -> list[dict]:
    
    if 'SOG_smoothed' not in boat_df.columns:
        boat_df['SOG_smoothed'] = boat_df['SOG'].rolling(window=smoothing_window, center=True, min_periods=1).mean()

    sog = boat_df['SOG_smoothed'].values
    time = boat_df['SecondsSince1970'].values
    twa = boat_df['TWA'].values
    cog = boat_df['COG'].values

    # Détection des minima (inversion de SOG)
    minima_idx, _ = find_peaks(-sog, prominence=prominence)
    maxima_idx, _ = find_peaks(sog, prominence=prominence)

    # Merge minima with entry SOG condition
    merged_minima = []
    for min_idx in minima_idx:
        min_time = time[min_idx]
        entry_time = max(min_time - pre_window, time[0])
        entry_idx = np.searchsorted(time, entry_time, side='left')

        entry_sog = sog[entry_idx]
        if entry_sog < min_sog_entry_threshold:
            continue  # Skip if entry speed is too low

        if not merged_minima:
            merged_minima.append(min_idx)
        else:
            time_diff = time[min_idx] - time[merged_minima[-1]]
            if time_diff >= min_minima_distance:
                merged_minima.append(min_idx)


    maneuvers = []
    for min_idx in merged_minima:
        left_max_candidates = [m for m in maxima_idx if m < min_idx]
        right_max_candidates = [m for m in maxima_idx if m > min_idx]

        if not left_max_candidates or not right_max_candidates:
            continue  # Skip if no flanking maxima

        min_time = time[min_idx]
        start_time = max(min_time - pre_window, time[0])
        end_time = min(min_time + post_window, time[-1])

        i1 = np.searchsorted(time, start_time, side='left')
        i2 = np.searchsorted(time, end_time, side='right')
        start_time = time[i1]
        end_time = time[i2]
        duration = end_time - start_time
        if duration < min_duration:
            continue

        # twa_start = abs(twa[i1])
        twa_min = abs(twa[min_idx])
        # twa_end = abs(twa[i2])
        cog_start = cog[i1]
        cog_end = cog[i2]
        window_size = 20
        twa_start = np.mean(np.abs(twa[i1:i1 + window_size])) if i1 + window_size < len(twa) else np.mean(np.abs(twa[i1:]))
        twa_end = np.mean(np.abs(twa[max(i2 - window_size, 0):i2])) if i2 - window_size >= 0 else np.mean(np.abs(twa[:i2]))

        # Calcul de la différence angulaire COG (avec gestion du wrap-around)
        cog_delta = abs(cog_end - cog_start)
        cog_delta = min(cog_delta, 360 - cog_delta)

        if cog_delta < cog_inversion_threshold:
            continue  # Pas de vraie inversion de cap

        # Classification de la manœuvre
        if twa_start > twa_threshold and twa_end > twa_threshold:
            mtype = "Jibe"
        elif twa_start < twa_threshold and twa_end < twa_threshold:
            mtype = "Tack"
        elif (twa_start < twa_threshold and twa_end > twa_threshold) or (twa_start > twa_threshold and twa_end < twa_threshold):
            mtype = "Buoy"
        else:
            mtype = "unknown"


        maneuvers.append({
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'maneuver_time': time[min_idx],
            'min_SOG': sog[min_idx],
            'TWA_start': twa_start,
            'TWA_min': twa_min,
            'TWA_end': twa_end,
            'COG_start': cog_start,
            'COG_end': cog_end,
            'COG_delta': cog_delta,
            'maneuver_type': mtype
        })

    return maneuvers
