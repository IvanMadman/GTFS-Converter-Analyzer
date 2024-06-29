import os
import zipfile
import pandas as pd
from sqlalchemy import create_engine
from database import create_tables, insert_data, create_engine_with_pool
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import filedialog, messagebox


logger = logging.getLogger(__name__)


# Setting low_memory to False it's not the BEST solution, but it works and should be enough for this context
def read_csv_file(file_path, file_name):
    try:
        df = pd.read_csv(file_path, low_memory=False)
        logger.info(f"Successfully read {file_name}")
        return df
    except pd.errors.EmptyDataError:
        logger.warning(f"File {file_name} is empty. Returning empty DataFrame.")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error reading file {file_name}: {e}")
        return None

# Before creating the file we ask for a name and check if there's one already
def get_database_engine():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

   
    db_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite database files", "*.db")])
    
    if not db_path:
        print("Operation cancelled.")
        return None
    
    if os.path.exists(db_path):
     
        if not messagebox.askyesno("Overwrite Confirmation", f"The file '{db_path}' already exists. Do you want to replace it?"):
            print("Operation cancelled.")
            return None
        else:
            os.remove(db_path)
    
    db_url = f"sqlite:///{db_path}"
    engine = create_engine_with_pool(db_url)
    print(f"Database engine created for {db_path}")
    return engine



# Right now if you want to grab more files you have to add it manually here and also in the database.py file
# I'll update this part with logic to get the file list during the zip extraction instead of expliciting it
def process_gtfs_file(zip_path, progress_callback):
    temp_dir = "temp_gtfs"
    
    try:
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        progress_callback(25)

        files = ["agency.txt", "stops.txt", "routes.txt", "trips.txt", "stop_times.txt", "calendar.txt", "calendar_dates.txt"]
        dataframes = {}

        # Use ThreadPoolExecutor for parallel file reading
        with ThreadPoolExecutor(max_workers=min(len(files), os.cpu_count() * 2)) as executor:
            future_to_file = {executor.submit(read_csv_file, os.path.join(temp_dir, file), file): file for file in files}
            for future in as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    df = future.result()
                    if df is not None:
                        table_name = file.split('.')[0]
                        dataframes[table_name] = df
                        logger.info(f"Processed {file}: {len(df)} rows")
                    else:
                        logger.warning(f"Skipping {file} due to reading error")
                except Exception as e:
                    logger.error(f"Error processing file {file}: {e}")

        progress_callback(75)

        

        # Use the new create_engine_with_pool function
        engine = get_database_engine()
        
        create_tables(engine)
        logger.info(f"tables created")
        insert_data(engine, dataframes)

        progress_callback(100)

    except Exception as e:
        logger.error(f"Error processing GTFS file: {e}")
        progress_callback(-1)  # Indicate error to the caller

    finally:
        # Clean up temporary directory
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)


