# F1 Qualifying Analysis
This project analyzes Formula 1 qualifying data to create interactive visualizations of driver performances across seasons. By collecting and processing data from qualifying sessions, it provides insights into drivers' qualifying positions, gaps to pole position, and teammate comparisons. The resulting dashboard allows users to explore each driver's career timeline, analyze their performance trends, and examine specific qualifying sessions in detail. 

The analysis focuses on key performance metrics including:
- Qualifying positions throughout seasons
- Time gaps to pole position
- Head-to-head teammate comparisons

Built using Python with FastF1 and Panel, this tool offers a comprehensive view of Formula 1 qualifying performances from 2018 to 2024.

## Quick Start
To view the pre-processed dashboard results directly:
```bash
git clone https://github.com/mvnye/F1-Qualifying-Analysis.git
cd F1-Qualifying-Analysis
pipenv shell
pipenv install
cd src
python dashboard.py
```

## Full Setup (For Data Collection and Processing)
If you want to collect and process new data:

1. Clone repository:
```bash
git clone https://github.com/mvnye/F1-Qualifying-Analysis.git
```

2. Navigate to the repository and install pipenv if not already installed:
```bash
cd F1-Qualifying-Analysis
pip install pipenv
```

3. Set up the virtual environment and install dependencies:
```bash
pipenv shell
pipenv install
```

4. Navigate to the src folder and run the data pipeline:
```bash
cd src
python data_collection.py --years 2018 2019 2020 2021 2022 2023 2024 --reload True
python data_processing.py 
python dashboard.py
```

## Scripts Overview
The project consists of three main Python scripts:

### data_collection.py
Downloads and organizes F1 qualifying data into CSV files for each year specified. 

The script implements error logging to track the data collection process. While FastF1 may generate error messages about driver lap timing inaccuracies during collection, these are expected behaviors and don't affect the overall dataset quality. The script will explicitly notify you if data collection fails for any specific year. 

Options:
- `--years` (Required): List of years (since 2018) to fetch data (e.g., 2021 2022 2023)
- `--cache-dir`: Directory for FastF1's cache (default: f1_cache)
- `--output-dir`: Directory to save fetched data (default: data)
- `--reload`: Whether to reload existing data (default: False)

Example usage:
```bash
python data_collection.py --years 2020 2021 2022 2023
```

### data_processing.py
Processes the raw qualifying data and creates the career timeline dataset to be used in dashboard creation. Options:
- `--input-dir`: Directory containing the raw CSV files (default: data)
- `--output-dir`: Directory for processed output (default: data)
- `--filename`: Name for the output file (default: career_timeline.json)

Example usage:
```bash
python data_processing.py 
```

### dashboard.py
Creates an interactive dashboard visualization for driver career timeline.

Example usage:
```bash
python dashboard.py 
```

## Dashboard Features and Usage
The interactive dashboard provides comprehensive qualifying analysis with several features:

### Main Features
- Driver career timeline with year-by-year analysis
- Qualifying position tracking throughout seasons (P1 indicates pole position)
- Gap to pole position analysis (time difference to P1)
- Teammate comparison metrics
- Best qualifying achievements per season
- Season summarization statistics
- Specific qualifying session results 

### How to Navigate
1. **Driver Selection**: Use the dropdown menu at the top of the screen to switch between drivers
2. **Year Sections**: For each year in the selected driver's career, you'll see:
   - Team information
   - Best qualifying position and where it was achieved
   - Average performance metrics
   - Interactive position graph
   - Event-specific details
3. **Event Details**: Use the dropdown menu in the lower right of each year section to view specific qualifying session results

## Data Structure
- Raw data is stored in CSV files in the data directory
- Processed data is saved as career_timeline.json in the data directory

For more information about project goals, background, and future work, see `WriteUp.pdf`
