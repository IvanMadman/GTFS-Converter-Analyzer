# GTFS Converter and Analyzer

![Screenshot of the TkinterUI of the app showing 2 buttons in a column, one to upload a GTFS file and one to upload a database ](/assets/images/TkinterUI.jpg)
![Screenshot of the Flask UI showing the landing page ](/assets/images/Flask_UI.jpg)

## Overview
The GTFS Converter and Analyzer is a Python/js application designed to work with static General Transit Feed Specification (GTFS) data. It offers two primary functionalities:

1. Converting GTFS zip files into SQL databases
2. Uploading GTFS databases to a Flask server with a user interface for searching stops and routes, viewing them on a map, and analyzing route statistics

## Features
- GTFS zip to SQL database conversion
- Web-based UI for data visualization and analysis
- Map integration for stop and route display (requires Google Maps API key)
- Route statistics including trip frequency and average estimated trip duration

## Dependencies
- Flask
- Flask-SQLAlchemy
- sqlalchemy
- Pandas
- ujson

## Installation
It is recommended to install this application in a virtual environment.

1. Clone the repository
2. Create and activate a virtual environment
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run main.py to launch
   ```
   python main.py
   ```

## Configuration
1. If you have a Google Maps API key, insert it into the `config.py` file.
2. To analyze additional data or create databases with more tables/rows:
   - Modify the `database.py` file to declare additional data following the existing pattern, when you will convert a new GTFS it will also look for those.
   - Add corresponding tables to the `server.py` file to enable the Flask server to access and analyze the new data.

## Usage

### Database Conversion
1. Launch the application to open the tkinter-based UI.
2. Click the button to upload a GTFS zip file.
3. Choose a name for the output database file when prompted.
4. Wait for the conversion process to complete. Note: The progress bar may pause at 75% during processing of the largest table.
You can look at the terminal to see how many rows it found and have a better understanding of the data size.
![Screenshot of the terminal window showing info about tables and rows found ](/assets/images/terminal.jpg)

### Data Analysis
1. Select an existing database and wait for it to load, the flask server window should open automatically in your browser
![Screenshot of the Flask UI showing the landing page ](/assets/images/Flask_UI.jpg)
2. The map tab lets you search for stops or routes and show it on map with markers. When selected, the routes will show the line connecting every stop
![Screenshot of the Flask UI showing a selected route and a line connecting all stops on the map ](/assets/images/polyline.jpg)
3. Use the web interface to:
   - Search for stops and routes
   - View stops and route lines on the map  (requires Google Maps API key)
   - Analyze route statistics with chart.js, including weekday trip frequencies and average estimated trip durations
![Screenshot of the Flask UI showing the statistics page with bar and round charts ](/assets/images/route_statistics.png)
P.S.
You can find additional info regarding the selected route inside Dev console
![Screenshot of the Dev console showing data on selected stops/routes ](/assets/images/devconsole1.jpg)
![Screenshot of the Dev console showing data on selected stops/routes ](/assets/images/devconsole2.jpg)
## Performance Considerations
- For large datasets (15-20 million rows and over), conversion may be time-consuming but it shouldnt take more than 2-3 minutes at most.
- The application uses ThreadPoolExecutor for parallel file reading and a QueuePool for efficient database insertion to optimize performance.
- If you need to change the selected database while the flask server it's already running, you can just select another file from the local ui and (hopefully) it should relaunch in a new window.

## Extensibility
The application is designed to be flexible. Users can modify `database.py` and `server.py` to accommodate additional GTFS data types or custom analysis requirements.

## Troubleshooting
- If the progress bar seems stuck at 75%, this is normal behavior while processing the largest table. Please be patient.
- Check the terminal window for additional information during database conversion.
- While you are using the webUI you can look in Dev console for additional info about selected values
- If you get strange warnings in Dev console remember to disable ad/script blockers and try again

## Contributing
Contributions to improve the GTFS Converter and Analyzer are welcome. Please feel free to submit pull requests or open issues for bugs and feature requests.

## License
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


