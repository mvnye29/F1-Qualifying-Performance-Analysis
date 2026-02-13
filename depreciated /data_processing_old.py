from pathlib import Path
import pandas as pd
import numpy as np
import logging
import argparse 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def combine_csv_files(folder_path: str | Path) -> pd.DataFrame | None:
    """
    Read all CSV files from a folder and combine them into a single DataFrame.
    
    Args:
        folder_path: Path to the folder containing CSV files
        
    Returns:
        Combined DataFrame from all CSV files or None if no files found
        
    Raises:
        FileNotFoundError: If the folder path doesn't exist
    """

    path = Path(folder_path)
    all_dfs = []
    
    for file in path.glob('*.csv'):
        try:
            df = pd.read_csv(file)
            all_dfs.append(df)
            print(f"Successfully read: {file.name}")
        except Exception as e:
            print(f"Error reading {file.name}: {str(e)}")
    
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        print(f"\nTotal number of files combined: {len(all_dfs)}")
        print(f"Total rows in DataFrame: {len(combined_df)}")
        return combined_df
    else:
        print("No CSV files found in the specified folder!")
        return None

def convert_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert time columns to timedelta and seconds.
    
    Args:
        df: DataFrame with time columns
        
    Returns:
        DataFrame with converted time columns
    """

    df['Q1'] = pd.to_timedelta(df['Q1'])
    df['Q2'] = pd.to_timedelta(df['Q2'])
    df['Q3'] = pd.to_timedelta(df['Q3'])

    df['Q1Seconds'] = df['Q1'].apply(lambda x: x.total_seconds() if pd.notna(x) else np.nan)
    df['Q2Seconds'] = df['Q2'].apply(lambda x: x.total_seconds() if pd.notna(x) else np.nan)
    df['Q3Seconds'] = df['Q3'].apply(lambda x: x.total_seconds() if pd.notna(x) else np.nan)   
    
    return df 

def get_best_time(driver_data: pd.Series) -> float | None:
    """
    Get best qualifying time from Q1, Q2, or Q3.

    Args:
        driver_data: Series containing driver's qualifying times
        
    Returns:
        Best qualifying time or None if no valid times
    """

    if pd.notna(driver_data.get('Q3Seconds')):
        return driver_data['Q3Seconds']
    elif pd.notna(driver_data.get('Q2Seconds')):
        return driver_data['Q2Seconds']
    elif pd.notna(driver_data.get('Q1Seconds')):
        return driver_data['Q1Seconds']
    return None

def calculate_gap_to_pole(position: float, best_time: float | None, pole_time: float) -> float:
    """
    Calculate gap to pole position.

    Args:
        position: Qualifying position
        best_time: Driver's best qualifying time
        pole_time: Pole position time
        
    Returns:
        Gap to pole in seconds
    """

    if pd.isna(position):
        return np.nan
    elif position == 1:
        return 0.0
    elif best_time is None or pd.isna(pole_time):
        return np.nan
    return best_time - pole_time

def create_event_summary(event_name: str, position: float, gap_to_pole: float, teammate_gap: float) -> dict:
    """
    Create event summary dictionary.

    Args:
        event_name: Name of the event
        position: Qualifying position
        gap_to_pole: Gap to pole position
        teammate_gap: Gap to teammate
        
    Returns:
        Dictionary with event summary data
    """

    return {
        'round': event_name,
        'position': position,
        'gapToPole': gap_to_pole,
        'teammateGap': teammate_gap,
        'hasTeammateData': not pd.isna(teammate_gap)
    }

def create_driver_entry(year: int, driver: str, team: str) -> dict:
    """
    Create initial driver entry dictionary.

    Args:
        year: Season year
        driver: Driver name
        team: Team name
        
    Returns:
        Dictionary with initial driver data
    """

    return {
        'year': year,
        'driver': driver,
        'team': team,
        'events': [],
        'positions': [],
        'gapToPole_values': [],
        'teammateGap_values': [],
        'completeDataCount': 0,
        'totalEvents': 0
    }

def calculate_teammate_gaps(team_data: pd.DataFrame) -> dict[str, float]:
    """
    Calculate gaps between teammates.
    
    Args:
        team_data: DataFrame containing team qualifying data
        
    Returns:
        Dictionary mapping driver names to time gaps with teammates
    """
    
    drivers = team_data['BroadcastName'].unique()
    gaps: dict = {driver: np.nan for driver in drivers}
    
    if len(drivers) == 2:
        driver1, driver2 = drivers
        driver1_data = team_data[team_data['BroadcastName'] == driver1]
        driver2_data = team_data[team_data['BroadcastName'] == driver2]
        
        if not driver1_data.empty and not driver2_data.empty:
            time1 = get_best_time(driver1_data.iloc[0])
            time2 = get_best_time(driver2_data.iloc[0])

            if time1 is not None and time2 is not None:
                gaps.update({
                    driver1: time1 - time2,
                    driver2: time2 - time1
                })
    
    return gaps

def process_qualifying_data(quali_data: pd.DataFrame) -> list[dict]:
    """
    Process qualifying data to create a timeline of driver performances.
    
    Args:
        quali_data: DataFrame containing qualifying session data
        
    Returns:
        List of dictionaries containing processed data for each driver's season
        
    Raises:
        ValueError: If required columns are missing from the input DataFrame
    """

    logger.info("Processing qualifying data...")
    timeline_data: list = []
    
    required_columns = [
        'DriverNumber', 'BroadcastName', 'TeamName', 'Position', 
        'Q1', 'Q2', 'Q3', 'Year', 'EventName', 'WetSession', 
        'Q1Seconds', 'Q2Seconds', 'Q3Seconds'
    ]
    
    missing_columns = [col for col in required_columns if col not in quali_data.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    
    driver_team_mapping = {}
    for year in quali_data['Year'].unique():
        year_data = quali_data[quali_data['Year'] == year]
        for _, row in year_data.iterrows():
            key = (year, row['BroadcastName'])
            if key not in driver_team_mapping:
                driver_team_mapping[key] = row['TeamName']

    for year in quali_data['Year'].unique():
        logger.info(f"Processing year: {year}")
        year_data = quali_data[quali_data['Year'] == year]
        
        all_events = year_data['EventName'].unique()
        
        year_drivers = set(year_data['BroadcastName'].unique())
        
        for driver in year_drivers:
            team = driver_team_mapping.get((year, driver))
            if team is None:
                continue
                
            driver_entry = create_driver_entry(year, driver, team)
            timeline_data.append(driver_entry)
            
            # Process each event for this driver
            for event_name in all_events:
                event_data = year_data[year_data['EventName'] == event_name]
                
                # Get pole time for the event
                pole_data = event_data[event_data['Position'] == 1]
                pole_time = pole_data.iloc[0]['Q3Seconds'] if not pole_data.empty else np.nan
                
                # Get driver's data for this event
                driver_event_data = event_data[event_data['BroadcastName'] == driver]
                
                if driver_event_data.empty:
                    # Driver didn't participate in this event
                    event_summary = create_event_summary(event_name, np.nan, np.nan, np.nan)
                else:
                    # Calculate gaps with teammates
                    team_data = event_data[event_data['TeamName'] == team]
                    gaps = calculate_teammate_gaps(team_data)
                    
                    driver_data = driver_event_data.iloc[0]
                    best_time = get_best_time(driver_data)
                    qualifying_position = driver_data['Position'] if pd.notna(driver_data['Position']) else np.nan
                    
                    gap_to_pole = calculate_gap_to_pole(qualifying_position, best_time, pole_time)
                    event_summary = create_event_summary(event_name, qualifying_position, gap_to_pole, gaps.get(driver, np.nan))
                    
                    if not pd.isna(gap_to_pole):
                        driver_entry['gapToPole_values'].append(gap_to_pole)
                    if not pd.isna(gaps.get(driver)):
                        driver_entry['teammateGap_values'].append(gaps[driver])
                        driver_entry['completeDataCount'] += 1
                
                driver_entry['events'].append(event_summary)
                driver_entry['positions'].append(event_summary['position'])
                driver_entry['totalEvents'] += 1
    
    # Calculate final statistics
    for entry in timeline_data:
        valid_positions = [pos for pos in entry['positions'] if not pd.isna(pos)]
        valid_gaps_to_pole = [gap for gap in entry['gapToPole_values'] if not pd.isna(gap)]
        valid_teammate_gaps = [gap for gap in entry['teammateGap_values'] if not pd.isna(gap)]
        
        entry['avgQualifyingPosition'] = np.mean(valid_positions) if valid_positions else np.nan
        entry['avgGapToPole'] = np.mean(valid_gaps_to_pole) if valid_gaps_to_pole else np.nan
        entry['avgTeammateGap'] = np.mean(valid_teammate_gaps) if valid_teammate_gaps else np.nan
        entry['dataCompleteness'] = entry['completeDataCount'] / entry['totalEvents'] if entry['totalEvents'] > 0 else 0
        
        # Clean up 
        for key in ['positions', 'gapToPole_values', 'teammateGap_values', 
                   'completeDataCount', 'totalEvents']:
            del entry[key]
    
    return timeline_data

def generate_dashboard_data(data_folder: str | Path, output_file: str | Path) -> None:
    """
    Generate and save dashboard data by running previous functions.

    Args:
        data_folder: Path to the folder containing raw CSV files.
        output_file: Path where the processed data will be saved as a JSON file.
    """
    logger.info("Generating dashboard data...")
    quali_data = combine_csv_files(data_folder)
    
    if quali_data is None:
        logger.error("No data processed: Failed to combine CSV files.")
        return
    
    quali_data = convert_time(quali_data)
    career_timeline_data = process_qualifying_data(quali_data)
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(career_timeline_data).to_json(output_path, orient='records', indent=4)

def main() -> None:
    """Main function to process F1 qualifying data and generate dashboard."""
    parser = argparse.ArgumentParser(description='Process F1 Qualifying Data')
    parser.add_argument('--input-dir', default='../data', help='Directory for input files')
    parser.add_argument('--output-dir', default='../data', help='Directory for output files')
    parser.add_argument('--filename', default='career_timeline.json', help='Filename for the output')
    
    args = parser.parse_args()
    
    generate_dashboard_data(args.input_dir, Path(args.output_dir) / args.filename)
    
    print(f"Dashboard data successfully generated and saved to {args.output_dir}/{args.filename}")
    
if __name__ == "__main__":
    main()