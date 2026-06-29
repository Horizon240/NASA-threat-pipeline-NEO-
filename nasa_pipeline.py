import requests
import psycopg2
from datetime import date, timedelta 
import gspread
import os
from dotenv import load_dotenv

load_dotenv()

#Database connection parameters
DB_URI = os.getenv("DB_URI")
GOOGLE_CREDS_FILE = "google_credentials.json"
SHEET_NAME = "Cosmic Threat Dashboard Data"

#Defining Data range 7 
start_date = date.today()
end_date = start_date+timedelta(days=7)

start_str = str(start_date)
end_str = str(end_date)


#The NASA API
url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_str}&end_date={end_str}&api_key=DEMO_KEY"

#Fetch data from nasa
try:
    response = requests.get(url)
    data = response.json()
except Exception as e:
    print(f"Failed to fetch data from NASA: {e}")

conn = None
cursor = None
#Connecting to the database
try:
    conn = psycopg2.connect(DB_URI)
    cursor = conn.cursor()

    #Looping throught the asteroids tracked today
    for date_key, neos in data['near_earth_objects'].items():
        for neo in neos:

            obj_id = neo['id']
            name = neo['name']                                                     #Extracting specific data
            is_hazardous = neo['is_potentially_hazardous_asteroid']
            close_approach = neo['close_approach_data'][0]
            velocity = float(close_approach['relative_velocity']['kilometers_per_second'])
            miss_distance = float(close_approach['miss_distance']['lunar'])

            #Inserting in SQL
            insert_query = """
                INSERT INTO neo_tracking (object_id, name, close_approach_date, velocity_km_s, miss_distance_lunar, is_potentially_hazardous)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (object_id) DO NOTHING;
            """

            cursor.execute(insert_query, (obj_id, name, date_key, velocity, miss_distance, is_hazardous))
    
    #Commiting
    conn.commit()
    print("Supabase: Raw data successfully loaded/verified")

    #transform data
    transform_query = """
        SELECT
            name,
            close_approach_date,
            velocity_km_s,
            miss_distance_lunar,
            is_potentially_hazardous,
            ROUND(((velocity_km_s / NULLIF(miss_distance_lunar,0)) * 10)::numeric,2) AS calculated_threat_score
        FROM
            neo_tracking
        WHERE 
            close_approach_date >= CURRENT_DATE 
        ORDER BY
            calculated_threat_score DESC
    """
    cursor.execute(transform_query)
    scored_data = cursor.fetchall()

    # 5. Load to Google Sheets for Tableau
    client = gspread.service_account(filename=GOOGLE_CREDS_FILE)
    
    # Open the spreadsheet (Double check Treat vs Threat in your Google Drive!)
    sheet = client.open(SHEET_NAME).sheet1
    
    # Clear any old data out of the sheet before writing fresh records
    sheet.clear()
    
    # Bundle headers and data into ONE massive list
    headers = ["Name", "Close Approach Date", "Velocity (km/s)", "Miss Distance (Lunar)", "Is Hazardous", "Threat Score"]
    
    full_data = [headers] # Start the list with headers at the top
    for row in scored_data:
        # Add each row of data underneath
        full_data.append([row[0], str(row[1]), row[2], row[3], str(row[4]), float(row[5])])
        
    # Push everything to the sheet in a single, bug-free API call
    if len(full_data) > 1:
        # Using explicit kwargs to ensure it works on any gspread version
        sheet.update(range_name="A1", values=full_data)
        print(f"Google Sheets: Successfully synced {len(scored_data)} records to '{SHEET_NAME}'!")
    else:
        print("Google Sheets: No records found to sync.")

except Exception as e:
    print(f"Database error: {e}")
finally:
    if conn:
        cursor.close()
        conn.close()
