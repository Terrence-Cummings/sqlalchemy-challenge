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
year_ago_latest = dt.datetime.strftime(year_ago_latest_dt, "%Y-%m-%d")

# What are the most active stations? (i.e. what stations have the most rows)?
stat_freq = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all()
max_stat_freq = stat_freq[0][0]

session.close()

#BEGIN FLASK APP
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def welcome():
    print("Server received request for 'Home' page...")
    return (
        f"Welcome to Surf's Up weather API!<br>"
        f"We collect precipitation and temperature data from weather stations on the island of Oahu in Hawaii.<br><br>"
        f"Earliest date of data = {earliest_date}<br>"
        f"Latest date of data = {latest_date}<br><br>"
        f"Available URL Routes:<br><br>"
        f"Below URL returns JSON of precipitation on Oahu on each day between {year_ago_latest} and {latest_date}.<br>"
        f"Copy this URL to browser: /api/v1.0/precipitation<br><br>"
        f"Below URL returns JSON of temperature on Oahu on each day between {year_ago_latest} and {latest_date}.<br>"
        f"Copy this URL to browser: /api/v1.0/temperature<br><br>"
        f"Below URL returns JSON of the weather stations on Oahu.<br>"
        f"Copy this URL to browser: /api/v1.0/stations<br><br>"
        f"Below URL returns the max, min, and avg temperature on Oahu encompassing the START and END dates provided by the user in the URL.<br>"
        f"If no END date provided in the URL then END date is assume to be {latest_date}<br>"
        f"Copy this URL to browser and replace START/END with dates in YYYY-MM-DD format: /api/v1.0/START/END"
    )


@app.route("/api/v1.0/precipitation/")
def precipitation():
    print("Server received request for 'Precipitation' page...")
    session = Session(engine)
    #Query precipitation observations for last year
    date_prcp_query = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date<=latest_date_dt).filter(Measurement.date>=year_ago_latest_dt)
    session.close()

    #Save as df and grab only the max precip observation for each day in the last year
    date_prcp_df = pd.DataFrame(date_prcp_query, columns=['Date', 'Precipitation'])
    date_prcp_df.set_index('Date', inplace=True)
    date_prcp_df.dropna(inplace=True)
    date_prcp_df.sort_index(inplace=True)
    date_prcp_max = date_prcp_df.groupby('Date')[['Precipitation']].max()
    #Turn into dictionary for jsonification
    prcp_query_dict = date_prcp_max.to_dict()

    return jsonify(prcp_query_dict)

@app.route("/api/v1.0/stations/")
def stations():
    print("Server received request for 'Stations' page...")
    session = Session(engine)
    #Query all the weather station details
    station_query = session.query(Station.station, Station.name, Station.latitude, Station.longitude, Station.elevation)
    station_df = pd.DataFrame(station_query, columns = ['station', 'name', 'latitude', 'longitude', 'elevation'])
    station_df.set_index('station', inplace=True)
    station_df.dropna(inplace=True)
    session.close()
    #Make a dictionary of weather station characteristics for jsonification
    station_dict = station_df.to_dict(orient='index')

    return jsonify(station_dict)

@app.route("/api/v1.0/temperature/")
def temperatures():
    print("Server received request for 'Temperatures' page...")

    session = Session(engine)
    #Query temperature observations for the last year at the station with the most observations
    tobs_date_query = session.query(Measurement.date, Measurement.tobs).\
    filter(Measurement.date<=latest_date_dt).filter(Measurement.date>=year_ago_latest_dt).\
    filter(Measurement.station==max_stat_freq)
    session.close()
    #Save query as df
    tobs_date_df = pd.DataFrame(tobs_date_query, columns=['Date','Temperature'])
    tobs_date_df.set_index('Date', inplace=True)
    tobs_date_df.dropna(inplace=True)
    #Transform df into dictionary for jsonification
    tobs_date_dict = tobs_date_df.to_dict()

    return jsonify(tobs_date_dict)

@app.route("/api/v1.0/<start>/")
def temp_start(start):
    #Control on START date within database date range
    if start<earliest_date or start>latest_date:
        return (
            f"START must be between {earliest_date} and {latest_date}.<br>"
            f"/api/v1.0/START"
        )

    print("Server received request for 'Min, Max, Avg Start End' page...")
    session = Session(engine)
    #Query max, min, and avg temperature between START date and last date in database
    TMAX = session.query(func.max(Measurement.tobs)).\
        filter(Measurement.date<=latest_date).filter(Measurement.date>=start).all()
    TMIN = session.query(func.min(Measurement.tobs)).\
        filter(Measurement.date<=latest_date).filter(Measurement.date>=start).all()
    TAVG = session.query(func.avg(Measurement.tobs)).\
        filter(Measurement.date<=latest_date).filter(Measurement.date>=start).all()
    session.close()
    #Round TAVG for presentation
    TAVG = round(TAVG[0][0],1)

    #Calc number of days in the query for information
    days_obs = latest_date_dt - dt.datetime.strptime(start, "%Y-%m-%d")
    days_obs = days_obs.days

    return  (
            f"The maximum temperature on Oahu for the {days_obs} days between {start} and {latest_date} was {TMAX[0][0]}.<br>"
            f"The minimum temperature on Oahu for the {days_obs} days between {start} and {latest_date} was {TMIN[0][0]}.<br>"
            f"The average temperature on Oahu for the {days_obs} days between {start} and {latest_date} was {TAVG}.<br>"
    )

@app.route("/api/v1.0/<start>/<end>/")
def temp_start_end(start, end):
    #Check START and END dates are within the range of database dates
    if start<earliest_date or start>latest_date or end<earliest_date or end>latest_date:
        return (
            f"START and END must be between {earliest_date} and {latest_date}.<br>"
            f"/api/v1.0/START/END"
        )
    #Allow for START and END interchanged in URL
    if end<start:
        start_temp = start
        start = end
        end = start_temp

    print("Server received request for 'Min, Max, Avg Start End' page...")
    session = Session(engine)
    #Query max, min, and avg temperature between START date and END date in database
    TMAX = session.query(func.max(Measurement.tobs)).\
        filter(Measurement.date<=end).filter(Measurement.date>=start).all()
    TMIN = session.query(func.min(Measurement.tobs)).\
        filter(Measurement.date<=end).filter(Measurement.date>=start).all()
    TAVG = session.query(func.avg(Measurement.tobs)).\
        filter(Measurement.date<=end).filter(Measurement.date>=start).all()
    session.close()
    #Round TAVG for presentation
    TAVG = round(TAVG[0][0],1)
    #Calc number of days in the query for information
    days_obs = dt.datetime.strptime(end, "%Y-%m-%d") - dt.datetime.strptime(start, "%Y-%m-%d")
    days_obs = days_obs.days

    return  (
            f"The maximum temperature on Oahu for the {days_obs} days between {start} and {end} was {TMAX[0][0]}.<br>"
            f"The minimum temperature on Oahu for the {days_obs} days between {start} and {end} was {TMIN[0][0]}.<br>"
            f"The average temperature on Oahu for the {days_obs} days between {start} and {end} was {TAVG}.<br>"
    )


if __name__ == "__main__":
    app.run(debug=True)


