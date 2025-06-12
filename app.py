from flask import Flask, jsonify, render_template, request, send_file
import os
import sqlite3 as sql

# the flask application: uses the webserver imported from the flask module:
app = Flask(__name__)

# constants: values that we need that won't change during the run:
DATABASE_FILE = "database.db"
DEFAULT_BUGGY_ID = "1"
BUGGY_RACE_SERVER_URL = "https://rhul.buggyrace.net"

#-----------------------------------------------------------------------------
# the home (or "index") page
#-----------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html", server_url=BUGGY_RACE_SERVER_URL)
#-----------------------------------------------------------------------------
# the info page
#-----------------------------------------------------------------------------
@app.route("/info")
def info():
    return render_template("info.html", server_url=BUGGY_RACE_SERVER_URL)
#-----------------------------------------------------------------------------
# the report page
#-----------------------------------------------------------------------------
@app.route('/report')
def report():
  return render_template("report.html", server_url=BUGGY_RACE_SERVER_URL)

#-----------------------------------------------------------------------------
# creating a new buggy:
#  * if it's a GET request, just show the form
#  * but if it's a POST request, process the submitted data
#-----------------------------------------------------------------------------
@app.route("/new", methods=["POST", "GET"])
def create_buggy():
    if request.method == "GET":
        db_connection = sql.connect(DATABASE_FILE)
        db_connection.row_factory = sql.Row
        cur = db_connection.cursor()
        cur.execute("SELECT * FROM buggies")
        record = cur.fetchone();         
        return render_template("buggy-form.html", buggy=record)
    elif request.method == "POST":
        message = ""
        qty_wheels = request.form["qty_wheels"].strip()
        flag_color = request.form["flag_color"]

        try:
            qty_wheels = int(qty_wheels)
            if qty_wheels < 4:
                raise ValueError("Wheel count must be a positive interger and at least 4, please re-enter wheel count")
        except ValueError:
            message = "Invalid wheel count, please enter a valid positive interger of at least 4"
            return render_template("buggy-form.html", msg=message, buggy=None)
        total_cost = qty_wheels * 50
        try:
            with sql.connect(DATABASE_FILE) as db_connection:
                cur = db_connection.cursor()
                cur.execute(
                    "UPDATE buggies set qty_wheels=?, flag_color=? WHERE id=?",
                    (qty_wheels, flag_color, DEFAULT_BUGGY_ID)
                )
                db_connection.commit()
        except sql.OperationalError as e:
            message = "Error in update operation: {e}"
            db_connection.rollback()
        else:
            message = "Record successfully saved"
        finally:
            db_connection.close()
        return render_template("updated.html", msg=message)

#-----------------------------------------------------------------------------
# a page for displaying the buggy
#-----------------------------------------------------------------------------
@app.route("/buggy")
def show_buggies():
    db_connection = sql.connect(DATABASE_FILE)
    db_connection.row_factory = sql.Row
    cur = db_connection.cursor()
    cur.execute("SELECT * FROM buggies")
    record = cur.fetchone(); 
    return render_template("buggy.html", buggy=record)

#-----------------------------------------------------------------------------
# get the JSON data that describes the buggy:
#  This reads the buggy record from the database, turns it into JSON format
#  (excluding any empty values), and returns it. There's no .html template
#  here because the response being sent only consists of JSON data.
#-----------------------------------------------------------------------------
@app.route("/json")
def send_buggy_json():
    db_connection = sql.connect(DATABASE_FILE)
    db_connection.row_factory = sql.Row
    cur = db_connection.cursor()
    cur.execute("SELECT * FROM buggies WHERE id=? LIMIT 1", (DEFAULT_BUGGY_ID))
    buggies = dict(
      zip([column[0] for column in cur.description], cur.fetchone())
    ).items() 
    return jsonify(
        {key: val for key, val in buggies if not (val == "" or val is None)}
    )

#-----------------------------------------------------------------------------
# send the favicon for the buggy editor:
# This sends the browser an icon image with a cache "time to live" of 24 hours,
# so you shouldn't see this being requested too often while you're debugging.
# There's no template here because it's sending a file straight back.
# (Usually you'd let Flask send images back as static content but this route
# adds the cache header as a special case).
#-----------------------------------------------------------------------------
@app.route("/favicon.png")
def send_favicon():
    return send_file(
        "static/favicon.png",
        mimetype='image/png',
        max_age=60*60*24
    )

#------------------------------------------------------------
# finally, after all the set-up above, run the app:
# This listens to the port for incoming HTTP requests, and sends a response
# back for each one. Unless something goes wrong, or you interrupt it (maybe
# with control-C), it will run forever... so any code you put _after_ app.run
# here won't normally be run.
if __name__ == "__main__":
    allocated_port = os.environ.get('BUGGY_EDITOR_PORT') or 5000
    app.run(debug=True, host="0.0.0.0", port=allocated_port)

