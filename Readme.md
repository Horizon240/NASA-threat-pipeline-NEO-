# NASA Near-Earth Object (NEO) Threat Pipeline



## Project Overview



An automated Extract, Load, Transform (ELT) data pipeline that pulls live telemetry data of Near-Earth Objects from NASA, processes it in a cloud PostgreSQL database, and visualizes the risk factors on a live Tableau dashboard.



\[Link to Live Tableau Dashboard] 

https://public.tableau.com/views/NASANear-EarthObjectThreatRadar/CosmicThreatDashboard?:language=en-US\&:sid=\&:redirect=auth\&:display\_count=n\&:origin=viz\_share\_link



## Architecture \& Technologies Used



* Data Extraction: Python (requests) pulling live JSON from the NASA REST API.
* Data Storage: Cloud PostgreSQL Data Warehouse (Supabase).
* Data Transformation: SQL queries used to clean data and engineer a custom Threat Score metric (Velocity / Lunar Miss Distance).
* Data Loading: Python (gspread, Google Cloud Service Accounts) pushing the transformed data into a Google Sheets reporting layer.
* Data Visualization: Tableau Public (Dark-mode scatter plot mapping speed vs. proximity).



## Pipeline Workflow



1. Extract: The Python script requests a 7-day rolling forecast of asteroids approaching Earth.
2. Load (Raw): Data is parsed and inserted into a Supabase PostgreSQL table using psycopg2, utilizing ON CONFLICT DO NOTHING to prevent duplicate records on subsequent runs.
3. Transform: A SQL query calculates a custom Risk/Threat Score based on relative velocity and miss distance.
4. Load (Analytics): The script connects to the Google Drive API and completely overwrites the target Google Sheet with the fresh, scored data.
5. Visualize: Tableau connects directly to the Google Sheet to display a live scatter plot.



## How to Run



1. Clone the repository.
2. Install dependencies: pip install requests psycopg2 gspread
3. Add your google\_credentials.json service account file to the root directory.
4. Update the DB\_URI with your Postgres connection string.
5. Run the pipeline: python nasa\_pipeline.py

