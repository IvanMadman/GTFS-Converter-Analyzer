from flask import Flask, render_template, request, jsonify, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from sqlalchemy import func, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import os
import ujson
from config import GOOGLE_MAPS_API_KEY

# Debugging line to check the value of DATABASE_URL
database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise EnvironmentError("DATABASE_URL environment variable not set.")


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Set up JSON encoder and decoder
app.json_encoder = ujson.dumps
app.json_decoder = ujson.loads

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Calendar(db.Model):
    __tablename__ = 'calendar'
    service_id = db.Column(db.String, primary_key=True)
    monday = db.Column(db.Boolean)
    tuesday = db.Column(db.Boolean)
    wednesday = db.Column(db.Boolean)
    thursday = db.Column(db.Boolean)
    friday = db.Column(db.Boolean)
    saturday = db.Column(db.Boolean)
    sunday = db.Column(db.Boolean)
    start_date = db.Column(db.String)
    end_date = db.Column(db.String)

class CalendarDate(db.Model):
    __tablename__ = 'calendar_dates'
    service_id = db.Column(db.String, primary_key=True)
    date = db.Column(db.Integer, primary_key=True)
    exception_type = db.Column(db.Integer)

class Stop(db.Model):
    __tablename__ = 'stops'
    stop_id = db.Column(db.String, primary_key=True)
    stop_name = db.Column(db.String)
    stop_lat = db.Column(db.Float)
    stop_lon = db.Column(db.Float)

class Route(db.Model):
    __tablename__ = 'routes'
    route_id = db.Column(db.String, primary_key=True)
    route_short_name = db.Column(db.String)
    route_long_name = db.Column(db.String)

class Trip(db.Model):
    __tablename__ = 'trips'
    trip_id = db.Column(db.String, primary_key=True)
    service_id = db.Column(db.String)
    route_id = db.Column(db.String, db.ForeignKey('routes.route_id'))
    direction_id = db.Column(db.Integer)
    stop_times = db.relationship('StopTime', backref='trip', lazy='joined')

class StopTime(db.Model):
    __tablename__ = 'stop_times'
    trip_id = db.Column(db.String, db.ForeignKey('trips.trip_id'), primary_key=True)
    arrival_time = db.Column(db.String)
    departure_time = db.Column(db.String)
    stop_id = db.Column(db.String, db.ForeignKey('stops.stop_id'))
    stop_sequence = db.Column(db.Integer, primary_key=True)
    stop_headsign = db.Column(db.String)
    pickup_type = db.Column(db.Integer)
    drop_off_type = db.Column(db.Integer)
    shape_dist_traveled = db.Column(db.String)
    timepoint = db.Column(db.Integer)

@app.route('/')
def index():
    return render_template('index.html', api_key=GOOGLE_MAPS_API_KEY)

# Simple search, gets all the routes and stops and returns it
@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query')
    stops = Stop.query.filter(Stop.stop_name.ilike(f'%{query}%')).all()
    routes = Route.query.filter(Route.route_short_name.ilike(f'%{query}%')).all()
    stops_data = [{'stop_id': stop.stop_id, 'stop_name': stop.stop_name, 'stop_lat': float(stop.stop_lat), 'stop_lon': float(stop.stop_lon)} for stop in stops]
    routes_data = [{'route_id': route.route_id, 'route_short_name': route.route_short_name, 'route_long_name': route.route_long_name} for route in routes]
    return jsonify({'stops': stops_data, 'routes': routes_data})


# This function it's used if the user selects another database while the server it's running,
# it will remove the existing one, reload and launch a new browser window
@app.route('/reload', methods=['POST'])
def reload_config():
    data = request.json
    db_path = data.get('db_path')
    if db_path:
        new_db_uri = f'sqlite:///{db_path}'
        
        with app.app_context():
            # Update the database URI in the app config
            app.config['SQLALCHEMY_DATABASE_URI'] = new_db_uri
            
            
            db.session.remove()
            
            # Dispose of the current engine
            db.engine.dispose()
            
            # Create a new engine
            engine = create_engine(new_db_uri)
            
            # Reconfigure the session and bind the new engine to the metadata
            db.session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
            db.metadata.bind = engine
            
            db.create_all()
        
        return jsonify({"message": "Database reloaded successfully"}), 200
    else:
        return jsonify({"error": "No db_path provided"}), 400

#This gets a list of stops associated with the route_id sent
@app.route('/stops', methods=['GET'])
def get_stops():
    route_id = request.args.get('route_id')
    if not route_id:
        return jsonify({'error': 'Missing route_id parameter'}), 400

    try:
        # Find the first trip_id for the given route_id and direction_id
        # We choose only one direction supposing the number should be more or less the same on both
        first_trip = (db.session.query(Trip)
                      .filter(Trip.route_id == route_id, Trip.direction_id == 0)
                      .order_by(Trip.trip_id)
                      .first())

        if not first_trip:
            return jsonify({'error': 'No trips found for the given route_id and direction_id'}), 404

        first_trip_id = first_trip.trip_id

        # Query stops associated with the first trip_id
        stops = (db.session.query(Stop.stop_id, Stop.stop_name, Stop.stop_lat, Stop.stop_lon)
                 .join(StopTime, Stop.stop_id == StopTime.stop_id)
                 .filter(StopTime.trip_id == first_trip_id)
                 .all())

        stop_list = [{
            'stop_id': stop.stop_id,
            'stop_name': stop.stop_name,
            'lat': stop.stop_lat,
            'lng': stop.stop_lon
        } for stop in stops]

        return jsonify(stop_list)

    except Exception as e:
        return jsonify({'error': f'An error occurred while retrieving stops: {e}'}), 500


# Here we analyze the data related to the route_id received, it can probably be 
# optimized more splitting it in multiple parts for better code understanding
@app.route('/route_info', methods=['GET'])
def route_info():
    route_id = request.args.get('route_id')
    if not route_id:
        return jsonify({'error': 'Missing route_id parameter'}), 400

    try:
        # Fetch distinct trips and stop times
        stop_times = db.session.query(
            Trip.trip_id,
            StopTime.arrival_time,
            StopTime.departure_time,
            StopTime.stop_sequence,
            Trip.service_id
        ).join(Trip, StopTime.trip_id == Trip.trip_id).filter(
            Trip.route_id == route_id,
            Trip.direction_id == 0
        ).order_by(
            Trip.trip_id,
            StopTime.stop_sequence
        ).all()

        if not stop_times:
            return jsonify({'error': 'No stop times found for the given route_id'}), 404

        trip_times = defaultdict(lambda: {'start_time': None, 'end_time': None})
        service_ids = {}
        # every time it finds a time where hours are 24+ it converts it 
        # So 25 becomes 01, 26-02 and so on
        def parse_time(time_str):
            hours, minutes, seconds = map(int, time_str.split(':'))
    
            if hours >= 24:
                days = hours // 24
                hours = hours % 24
                return datetime.strptime(f"{hours:02d}:{minutes:02d}:{seconds:02d}", '%H:%M:%S') + timedelta(days=days)
            else:
                return datetime.strptime(time_str, '%H:%M:%S')

        for trip_id, arrival_time, departure_time, stop_sequence, service_id in stop_times:
            service_ids[trip_id] = service_id
            try:
                arrival_obj = parse_time(arrival_time)
                departure_obj = parse_time(departure_time)

                if trip_times[trip_id]['start_time'] is None or stop_sequence == 1:
                    trip_times[trip_id]['start_time'] = arrival_obj
                trip_times[trip_id]['end_time'] = departure_obj
            except ValueError as e:
                logger.error(f'Error parsing time for trip_id {trip_id}: {e}')
                continue

        # Process working days from calendar and calendar_dates
        working_days = defaultdict(lambda: defaultdict(list))

        for service_id in set(service_ids.values()):
            calendar = Calendar.query.filter_by(service_id=service_id).first()
            if calendar:
                for day, active in enumerate([calendar.monday, calendar.tuesday, calendar.wednesday, calendar.thursday, calendar.friday, calendar.saturday, calendar.sunday]):
                    if active:
                        working_days[service_id][day].append(service_id)
            else:
                calendar_dates = CalendarDate.query.filter_by(service_id=service_id).all()
                for cd in calendar_dates:
                    date = datetime.strptime(str(cd.date), '%Y%m%d')
                    day = date.weekday()
                    if cd.exception_type == 1:
                        working_days[service_id][day].append(service_id)

        # Trips by day of the week
        trips_by_day_dict = {str(i): 0 for i in range(7)}

        for trip_id in trip_times.keys():
            service_id = service_ids[trip_id]
            if service_id in working_days:
                for day in working_days[service_id]:
                    trips_by_day_dict[str(day)] += 1

        trips_by_day_list = [trips_by_day_dict[str(i)] for i in range(7)]

        # Average route times by day of the week
        avg_route_time_by_day = defaultdict(list)
        for trip_id, times in trip_times.items():
            start_time = times['start_time']
            end_time = times['end_time']
            if start_time and end_time:
                if end_time < start_time:
                    end_time += timedelta(days=1)
                route_time = (end_time - start_time).total_seconds() / 60

                service_id = service_ids[trip_id]
                if service_id in working_days:
                    for day in working_days[service_id]:
                        avg_route_time_by_day[day].append(route_time)

        avg_route_times = [sum(times) / len(times) if times else 0.0 for times in [avg_route_time_by_day[day] for day in range(7)]]

        return jsonify({
            'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
            'tripsByDay': trips_by_day_list,
            'avgRouteTime': avg_route_times
        })

    except Exception as e:
        logger.error(f"Error retrieving route info for route {route_id}: {e}", exc_info=True)
        return jsonify({'error': 'An error occurred while retrieving route info'}), 500



@app.route('/routes')
def get_routes():
    routes = Route.query.all()
    return jsonify([{'route_id': route.route_id, 'route_short_name': route.route_short_name, 'route_long_name': route.route_long_name} for route in routes])



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False)
