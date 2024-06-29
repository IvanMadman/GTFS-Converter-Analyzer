from sqlalchemy import Table, Column, Integer, String, MetaData, create_engine, PrimaryKeyConstraint
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
import logging



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

metadata = MetaData()

#The app will only grab those tables and columns from the GTFS files, if you need more you can add it here.
#Everything not listed here will be skipped

def create_tables(engine):
    global metadata

    
    agency = Table('agency', metadata,
        Column('agency_id', String, primary_key=True),
        Column('agency_name', String),
        Column('agency_url', String),
        Column('agency_timezone', String),
        Column('agency_lang', String),
        Column('agency_phone', String),
        Column('agency_email', String),
        Column('agency_fare_url', String)
    )

    stops = Table('stops', metadata,
        Column('stop_id', String, primary_key=True),      
        Column('stop_code', String),
        Column('stop_name', String),
        Column('tts_stop_name', String),
        Column('stop_desc', String),
        Column('stop_lat', String),
        Column('stop_lon', String),
        Column('zone_id', String),
        Column('stop_url', String),
        Column('wheelchair_boarding', Integer),
        Column('stop_timezone', String),
        Column('location_type', Integer),
        Column('level_id', Integer),
        Column('platform_code', String),
        Column('parent_station', String)
    )

    routes = Table('routes', metadata,
        Column('route_id', String, primary_key=True),
        Column('agency_id', String),
        Column('route_short_name', String),
        Column('route_long_name', String),
        Column('route_desc', String),
        Column('route_type', Integer),
        Column('route_url', String),
        Column('route_color', String),
        Column('route_text_color', String)
    )

    trips = Table('trips', metadata,
        Column('route_id', String),
        Column('service_id', String),
        Column('trip_id', String, primary_key=True),
        Column('trip_headsign', String),
        Column('trip_short_name', String),
        Column('direction_id', Integer),
        Column('block_id', String),
        Column('shape_id', String),
        Column('wheelchair_accessible', Integer),
        Column('exceptional', Integer)
    )

    stop_times = Table('stop_times', metadata,
        Column('trip_id', String, primary_key=True),
        Column('arrival_time', String),
        Column('departure_time', String),
        Column('stop_id', String),
        Column('stop_sequence', Integer, primary_key=True),
        Column('stop_headsign', String),
        Column('pickup_type', Integer),
        Column('drop_off_type', Integer),
        Column('shape_dist_traveled', String),
        Column('timepoint', Integer),
        PrimaryKeyConstraint('trip_id', 'stop_sequence')
    )

    calendar = Table('calendar', metadata,
        Column('service_id', String, primary_key=True),
        Column('monday', Integer),
        Column('tuesday', Integer),
        Column('wednesday', Integer),
        Column('thursday', Integer),
        Column('friday', Integer),
        Column('saturday', Integer),
        Column('sunday', Integer),
        Column('start_date', String),
        Column('end_date', String)
    )
    
    calendar_dates = Table('calendar_dates', metadata,
        Column('service_id', String, primary_key=True),
        Column('date', Integer, primary_key=True),
        Column('exception_type', Integer)
    )

    
    metadata.create_all(engine)

# Before inserting the data we filter it to only get the tables/rows listed above here
# The processing speed of this part can probably be enhanced  with some optimizations

def insert_data(engine, dataframes):
    global metadata
    
    with engine.begin() as conn:
        for table_name, dataframe in dataframes.items():
            if table_name in metadata.tables:
                table = metadata.tables[table_name]
                
                # Filter dataframe columns to match the table columns
                table_columns = set(column.name for column in table.columns)
                df_columns = set(dataframe.columns)
                valid_columns = list(table_columns.intersection(df_columns))
                
                filtered_df = dataframe[valid_columns]
                
                # Converting dataframe to a list of dicts and then splitting the data insertion in chunks to speed up.
                # Chuck_size can be modified as needed, raising or lowering it will (should) impact the time needed to complete the inserts
                try:
                    
                    data = filtered_df.to_dict('records')
                    
                    chunk_size = 50000  
                    for i in range(0, len(data), chunk_size):
                        chunk = data[i:i+chunk_size]
                        result = conn.execute(table.insert(), chunk)
                    
                    logger.info(f"Inserted {len(data)} rows into {table_name}")
                except SQLAlchemyError as e:
                    logger.error(f"Error inserting data into {table_name}: {str(e)}")
            else:
                logger.warning(f"Table '{table_name}' not found in metadata.")


#Pooling should give a better performance in this context
#
def create_engine_with_pool(db_url):
    return create_engine(db_url, poolclass=QueuePool, pool_size=50, max_overflow=100)
