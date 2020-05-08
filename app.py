#Dependencies, libraries, and imports
from matplotlib import style
style.use('fivethirtyeight')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime as dt

#SQLalchemy libraries and functions
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect, MetaData
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

#VROOM, VROOM!
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

#Use automap to get table structures and reflect into classes
Base = automap_base()
Base.prepare(engine, reflect=True)

#See what classes have been created. Classes created should match tables found by Inspector
classes_created = Base.classes.keys()

#Single variable to represent each Class associated with the automapped Base
Measurement = Base.classes.measurement
Station = Base.classes.station

#Classes are now all setup. Start query session.
session = Session(engine)

# Design a query to retrieve the last 12 months of precipitation data and plot the results

#Find the earliest date in the Measurement table by query. Convert to python dictionary, read date as text, convert to datetime.
earliest_date_query = session.query(Measurement.date).order_by(Measurement.date).first()
ed_dict=earliest_date_query._asdict()
earliest_date = ed_dict['date']
earliest_date_dt = dt.datetime.strptime(earliest_date, "%Y-%m-%d")

#Find the latest date in the Measurement table by query. Convert to python dictionary, read date as text, convert to datetime.
latest_date_query = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
ld_dict=latest_date_query._asdict()
latest_date = ld_dict['date']
latest_date_dt = dt.datetime.strptime(latest_date, "%Y-%m-%d")

# Calculate the date 1 year ago from the latest data point in the database
year_ago_latest_dt = latest_date_dt - dt.timedelta(days=365)

# What are the most active stations? (i.e. what stations have the most rows)?
stat_freq = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all()
max_stat_freq = stat_freq[0][0]

# highest temp recorded, and average temp of the most active station?
max_temp_max_stat = session.query(Measurement.station, func.max(Measurement.tobs)).filter(Measurement.station==max_stat_freq).all()
min_temp_max_stat = session.query(Measurement.station, func.min(Measurement.tobs)).filter(Measurement.station==max_stat_freq).all()
avg_temp_max_stat = session.query(Measurement.station, func.avg(Measurement.tobs)).filter(Measurement.station==max_stat_freq).all()

session.close()

#BEGIN FLASK APP
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def welcome():
    print("Server received request for 'Home' page...")
    return (
        f"Welcome to Surf's Up weather API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/temperature<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>" 
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    print("Server received request for 'Precipitation' page...")
    session = Session(engine)
    date_prcp_query = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date<=latest_date_dt).filter(Measurement.date>year_ago_latest_dt)
    session.close()

    date_prcp_df = pd.DataFrame(date_prcp_query, columns=['Date', 'Precipitation'])
    date_prcp_df.set_index('Date', inplace=True)
    date_prcp_df.dropna(inplace=True)
    date_prcp_df.sort_index(inplace=True)
    date_prcp_max = date_prcp_df.groupby('Date')[['Precipitation']].max()
    prcp_query_dict = date_prcp_max.to_dict()

    return jsonify(prcp_query_dict)

@app.route("/api/v1.0/stations")
def stations():
    print("Server received request for 'Stations' page...")
    session = Session(engine)
    station_names = session.query(Station.name).all()
    session.close()
    all_stats = list(np.ravel(station_names))
    return jsonify(all_stats)

@app.route("/api/v1.0/temperature")
def temperatures():
    print("Server received request for 'Temperatures' page...")

    session = Session(engine)
    tobs_date_query = session.query(Measurement.date, Measurement.tobs).\
    filter(Measurement.date<=latest_date_dt).filter(Measurement.date>=year_ago_latest_dt).\
    filter(Measurement.station==max_stat_freq)
    session.close()

    tobs_date_df = pd.DataFrame(tobs_date_query, columns=['Date','Temperature'])
    tobs_date_df.set_index('Date', inplace=True)
    tobs_date_df.dropna(inplace=True)
    tobs_date_dict = tobs_date_df.to_dict()

    return jsonify(tobs_date_dict)

@app.route("/api/v1.0/<start>")
def temp_start():
    print("Server received request for 'Min, Max, Avg Start' page...")
    return "Welcome to the Min, Max, Avg Start Date page!"

@app.route("/api/v1.0/<start>/<end>")
def temp_start_end():
    print("Server received request for 'Min, Max, Avg Start End' page...")
    return "Welcome to the Min, Max, Avg Start End Date page!"

if __name__ == "__main__":
    app.run(debug=True)


