from flask import Flask, request, jsonify, render_template
import subprocess
import os
from gsheet import *

app = Flask(__name__, static_folder=os.path.join(os.getcwd(), 'static'))

# Requires the PyMongo package.
# https://api.mongodb.com/python/current

coll_procedure_risk = db[mongo_db_coll_procedure_risk]
coll_sun_sensitivity = db[mongo_db_coll_sun_sensitivity]
coll_hq = db[mongo_db_coll_hq]
coll_retinol = db[mongo_db_coll_retinol]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add')
def add_numbers():
    x = int(request.args.get('x'))
    y = int(request.args.get('y'))
    z = x + y
    return jsonify({'result': z})

@app.route('/run_script', methods=['POST'])
def run_script():
    action = request.form['action']
    print(action)
    script = 'run_ingestion.sh'
    param1 = ''
    if action == 'ingest_update':
        param1 = 'true' 
        message = 'Version Update/Data Update Successful'
    elif action == 'ingest_new_data':
        param1 = 'false'
        message = 'Release Update/New Data Ingestion Successful'
    else:
        message = 'Invalid action'   
    subprocess.run(["bash", script, param1], check=True)     
    return jsonify(message=message)

@app.route('/patient_page')
def patient_page():
    return render_template('patient_details.html')

@app.route('/submit', methods=['POST'])
def submit_form():
    data = request.get_json()
    # Process the form data as needed
    print(data)

    sun_sensitivity= coll_sun_sensitivity.find_one({"Sun Sensitivity": data['sun_sensitivity']})['Values']
    retinol_adequate = coll_retinol.find_one({"Retinol": str(data['retinol_adequate']), "Category": "Adequate"})['Values']
    print(retinol_adequate)
    retinol_inadequate = coll_retinol.find_one({"Retinol": str(data['retinol_inadequate']), "Category": "Inadequate"})['Values']
    print(retinol_inadequate)
    hq = coll_hq.find_one({"Hq 4%": data['hq']})['Values']
    if data['sun']=='yes':
        sun_protection = 15
    else:
        sun_protection = 0
    print(sun_sensitivity, retinol_adequate, retinol_inadequate, hq)
    client_score = 0
    if data['sun_sensitivity'] == "Dark Brown":
        client_score = sun_sensitivity - 0.3*(sun_protection+retinol_adequate+retinol_inadequate+hq)
    elif data['sun_sensitivity'] == 'Black':
        client_score = sun_sensitivity - 0.5*(sun_protection+retinol_adequate+retinol_inadequate+hq)
    else:
        client_score = sun_sensitivity - (sun_protection+retinol_adequate+retinol_inadequate+hq)
    # Return a response (e.g., success message)
    return jsonify({'client-score': f"{client_score}"})


if __name__ == '__main__':
    app.run(debug=True)
