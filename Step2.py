import numpy as np
import pandas as pd

import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# We can view all of the classes that automap found
Base.classes.keys()

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#Getting the date for 1 year ago.
last_day = session.query(func.max(Measurement.date)).all()[0][0]
last_day_dt = dt.datetime.strptime(last_day,'%Y-%m-%d')

year_ago = last_day_dt - dt.timedelta(days=366)
year_ago_str = year_ago.strftime("%Y-%m-%d")


# Calculate the date 1 year ago from the last data point in the database
measurement_Q_prcp = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date > year_ago_str).order_by(Measurement.date).all()

m_df = pd.DataFrame(measurement_Q_prcp, columns=['Date','Precipitation'])
m_df.set_index('Date', inplace=True)


#Ok, flask app down here:

#imports and basics
from flask import Flask, jsonify
app = Flask(__name__)

#Routes, home route
@app.route("/")
def home():
  print("Server received request for 'Home' page...")
  return "<h1>Routes available<h1><br><br>\
  				<a href='/api/v1.0/precipitation'>Precipitation API link</a><br><br>\
  				<a href='/api/v1.0/stations'>Stations API link</a><br><br>\
  				<a href='/api/v1.0/tobs'>Temperature API link</a><br><br>\
  				<a href='/api/v1.0/2014-12-31'>/api/v1.0/start <-- This thing here. Use YYYY-MM-DD in place of start</a>\
  				<br>\
  				<div>Sample date already put in.</div>\
  				<br>\
  				<a href='/api/v1.0/2010-01-01/2014-01-01'> /api/v1.0/start/end <-- This thing here. Use YYYY-MM-DD in place of start and end</a><br><br>\
  				"

@app.route("/api/v1.0/precipitation")
def precipitation():
	#we have to recreate the session object here otherwise we get threading issues
	#https://stackoverflow.com/questions/48218065/programmingerror-sqlite-objects-created-in-a-thread-can-only-be-used-in-that-sa
	session = Session(engine)
	query_results = session.query(Measurement.date, Measurement.prcp).all()

	dictionaried_query_results = { i[0] : i[1] for i in query_results }
	return jsonify(dictionaried_query_results)

@app.route("/api/v1.0/stations")
def stations():
	session = Session(engine)
	query_results = session.query(Station.station).all()

	#Let me flatten it real fast...
	import itertools
	flat_list = list(itertools.chain(*query_results))

	return jsonify(flat_list)

@app.route("/api/v1.0/tobs")
def tobs():
	session = Session(engine)
	query_results = session.query(Measurement.date, Measurement.tobs).\
	filter(Measurement.date > year_ago_str).\
	all()

	return jsonify(query_results)

#dynamic routing
@app.route("/api/v1.0/<start>")
def avg_temps_start_only(start):

	#So we have to convert start into a DT object below or else the filter won't work.
	start_dt = dt.datetime.strptime(start,'%Y-%m-%d')

	session = Session(engine)

	query = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
  filter(Measurement.date >= start_dt).all()

	print("Query Results is: ")
	print(query)

	return jsonify(query)

@app.route("/api/v1.0/<start>/<end>")
def avg_temps_start_and_end(start,end):
	session = Session(engine)
	start_dt = dt.datetime.strptime(start,'%Y-%m-%d')
	end_dt = dt.datetime.strptime(end,'%Y-%m-%d')

	query = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
  filter(Measurement.date >= start_dt).filter(Measurement.date <= end_dt).all()

	return jsonify(query)

#Run app at the bottom
if __name__ == "__main__":
    app.run(debug=True)
