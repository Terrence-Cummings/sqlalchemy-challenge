from flask import Flask

app = Flask(__name__)

@app.route("/")
def welcome():
    print("Server received request for 'Home' page...")
    return (
        f"Welcome to Surf's Up weather API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
        
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    print("Server received request for 'Precipitation' page...")
    return "Welcome to the Precipitation page!"

@app.route("/api/v1.0/stations")
def stations():
    print("Server received request for 'Stations' page...")
    return "Welcome to the Stations page!"

@app.route("/api/v1.0/tobs")
def temperatures():
    print("Server received request for 'Temperatures' page...")
    return "Welcome to the Temperatures page!"

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


