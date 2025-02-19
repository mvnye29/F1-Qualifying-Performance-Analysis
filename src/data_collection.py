import fastf1
import pandas as pd
import logging
import time
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import argparse
import gc
import sys



class F1DataFetcher:
    def __init__(self, cache_dir: str = 'f1_cache', 
                 output_dir: str = 'f1_data', 
                 reload: bool = False) -> None:
        """
        Initialize F1 data fetcher.
        
        Args:
            cache_dir: Directory for FastF1 cache
            output_dir: Directory for output CSV files
            reload: If True, reload data 
        """
        
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.reload = reload

        # Create directories with parent directories if needed
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        
        # Setup logging
        self._setup_logging()
        
        # Initialize FastF1
        self._setup_fastf1()
        
    def _setup_logging(self) -> None:
        """Configure logging for errors."""

        log_file = self.output_dir / 'data_collection.log'
    
        # Configure root loggerW
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.ERROR)
        
        # Set format for logs
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Configure file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        
        # Configure console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Suppress all other loggers
        for logger_name in logging.root.manager.loggerDict:
            logging.getLogger(logger_name).setLevel(logging.Error)
        
        # Create our specific logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _setup_fastf1(self)  -> None:
        """Initialize FastF1 with cache."""

        try:
            fastf1.Cache.enable_cache(str(self.cache_dir))
        except Exception as e:
            self.logger.error(f"Failed to initialize FastF1 cache: {e}")
            sys.exit(1)
    
    def fetch_qualifying_data(self, years: list[int]) -> dict[str, list[int]]:
        """
        Fetch qualifying data for specified years.
        
        Args:
            years (list): List of years to fetch data for
        Returns:
            dict: Dictionary with 'success' and 'failed' year lists
        """

        results = {'success': [], 'failed': []}
        
       
        for year in years:
            try:
                output_file = self.output_dir / f'qualifying_data_{year}_results.csv'
                    
                # Skip if file exists and reload is False
                if output_file.exists() and not self.reload:
                    self.logger.info(f"Data for {year} already exists, skipping...")
                    results['success'].append(year)
                    continue
                    
                # Get schedule for the year
                schedule = self._get_schedule(year)
                if schedule is None:
                    results['failed'].append(year)
                    continue
                    
                 # Process each event
                yearly_data = self._process_year_events(year, schedule)
                    
                if yearly_data:
                    # Save each year to CSV
                    yearly_df = pd.concat(yearly_data, ignore_index=True)
                    yearly_df.to_csv(output_file, index=False)
                        
                    results['success'].append(year)
                else:
                    results['failed'].append(year)
                        
            except Exception as e:
                self.logger.error(f"Failed to process {year}: {str(e)}")
                results['failed'].append(year)
            finally:
                gc.collect()  # Clear memory after each year
        
        return results
    
    def _get_schedule(self, year: int, max_retries: int = 3, delay: int = 5) -> pd.DataFrame | None:
        """
        Get event schedule with retry logic.
        
        Args:
            year: Year to fetch schedule for
            max_retries: Maximum number of retry attempts
            delay: Delay between retries in seconds
            
        Returns:
            DataFrame of schedule or None if failed
        """

        for attempt in range(max_retries):
            try:
                schedule = fastf1.get_event_schedule(year)
                
                # Filter schedule
                schedule = schedule[schedule['EventFormat'] != 'testing']
                if datetime.now().year == year:
                    schedule = schedule[schedule['EventDate'] < datetime.now()]
                
                return schedule
                
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed for {year}. "
                        f"Retrying in {delay} seconds..."
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(f"Failed to get {year} schedule: {str(e)}")
                    return None
    
    def _process_year_events(self, year: int, schedule: pd.DataFrame) -> list[pd.DataFrame]:
        """
        Process all events for a given year.
        
        Args:
            year: Year to process
            schedule: DataFrame containing event schedule
            
        Returns:
            list: List of DataFrames containing event data
        """

        yearly_data = []

        for _, event in schedule.iterrows():
            try:
                time.sleep(5)  # attempt at rate limiting 
                
                session = fastf1.get_session(year, event['EventName'], 'Q')
                session.load()

                laps = session.laps 
                weather_data = session.weather_data

                # Determine if session is wet based on rainfall 
                is_wet = False
                if weather_data is not None and 'Rainfall' in weather_data.columns:
                    session_weather = weather_data  
                    if not session_weather.empty:
                        rain_percentage = session_weather['Rainfall'].mean()
                        is_wet = rain_percentage > 0.5

                # get relevant columns from session.results
                results_data = session.results[['DriverNumber', 'BroadcastName', 'TeamName', 
                                          'Position', 'Q1', 'Q2', 'Q3']].copy()
            
                # Add event and weather information
                results_data['Year'] = year
                results_data['EventName'] = event['EventName']
                results_data['WetSession'] = is_wet
            
                yearly_data.append(results_data)

            except Exception as e:
                self.logger.error(f"Error loading {event['EventName']} {year}: {str(e)}")

        return yearly_data
def main() -> None:
    """Main function to run the F1 data fetcher."""

    parser = argparse.ArgumentParser(description='Fetch F1 Quali Data')
    parser.add_argument('--years', nargs='+', type=int, required=True,
                      help='Years to fetch data for')
    parser.add_argument('--cache-dir', default='f1_cache',
                      help='Directory for FastF1 cache')
    parser.add_argument('--output-dir', default='../data',
                      help='Directory for output files')
    parser.add_argument('--reload', type=bool, default= False,
                      help='Reload existing data')
    
    args = parser.parse_args()
    
    fetcher = F1DataFetcher(
        cache_dir=args.cache_dir,
        output_dir=args.output_dir,
        reload=args.reload
    )
    
    results = fetcher.fetch_qualifying_data(args.years)
    
    print("\nData Collection Summary:")
    print(f"Successfully processed years: {results['success']}")
    print(f"Failed years: {results['failed']}")

if __name__ == "__main__":
    main()