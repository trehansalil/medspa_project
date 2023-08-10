from flask import Flask, request, jsonify, render_template
import subprocess
import os
import pandas as pd
from datetime import datetime
from gsheet import *

app = Flask(__name__, static_folder=os.path.join(os.getcwd(), 'static'))

# Requires the PyMongo package.
# https://api.mongodb.com/python/current

coll_procedure_risk = db[mongo_db_coll_procedure_risk]
coll_sun_sensitivity = db[mongo_db_coll_sun_sensitivity]
coll_hq = db[mongo_db_coll_hq]
coll_retinol = db[mongo_db_coll_retinol]
coll_sun_protection = db[mongo_db_coll_sun_protection]

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
    param2 = request.form['admin_comments']
    print(f"Action = {action}, comments = {param2}")
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
    subprocess.run(["bash", script, param1, param2], check=True)     
    return jsonify(message=message)

@app.route('/patient_page')
def patient_page():
    return render_template('patient_details4.html')

@app.route('/submit', methods=['POST'])
def submit_form():
    data = request.get_json()
    # Process the form data as needed

    data['tel'] = data['tel'].replace(" ", "").strip()
    data['name'] = data['name'].replace("  ", " ").strip().title()
    data['email'] = data['email'].lower().strip() 

    data['_id'], data['_is_new'], prev_recos = generate_custom_id(name=data['name'], email=data['email'], phone=data['tel'])
    if data['_is_new']:
        data['created_at'] = datetime.now() 
        data['updated_at'] = data['created_at']
    else:
        data['updated_at'] = datetime.now()


    sun_sensitivity= coll_sun_sensitivity.find_one({"Sun Sensitivity": data['sun_sensitivity']})['Values']
    retinol_adequate = coll_retinol.find_one({"Retinol": str(data['retinol_adequate']), "Category": "Adequate"})['Values']
    print(retinol_adequate)
    retinol_inadequate = coll_retinol.find_one({"Retinol": str(data['retinol_inadequate']), "Category": "Inadequate"})['Values']
    print(retinol_inadequate)
    sun_protection = coll_sun_protection.find_one({"Sun Protection": str(data['sun_protection'])})['Values']
    hq = coll_hq.find_one({"Hq 4%": data['hq']})['Values']
    # if data['sun']=='yes':
    #     sun_protection = 15
    # else:
    #     sun_protection = 0
    print(sun_sensitivity, retinol_adequate, retinol_inadequate, hq)
    client_score = 0

    if data['sun_sensitivity'] == "Dark Brown":
        client_score = sun_sensitivity - 0.3*(sun_protection+retinol_adequate+retinol_inadequate+hq)
    elif data['sun_sensitivity'] == 'Black':
        client_score = sun_sensitivity - 0.5*(sun_protection+retinol_adequate+retinol_inadequate+hq)
    else:
        client_score = sun_sensitivity - (sun_protection+retinol_adequate+retinol_inadequate+hq)
    client_score = client_score if client_score>0 else 0

    data['latest_client_score'] = client_score
    
    json_data = []
    # if data['key'] == "Procedure" key = "procedure" elif data['key'] == 'PIH Risk' key = "pih_risk" elif data['key'] == 'PIH & Procedure Risk' key = "pih_procedure_risk" else 
    key_dict = {"Procedure": 'procedure',
                "PIH Risk": 'pih_risk',
                "PIH & Procedure Risk": 'pih_procedure_risk',
                "Frekles": 'Frekles',
                "LHR": 'LHR',
                "CIT of Procedure": 'cit_of_procedure',
                "Melasma": 'Melasma'}
    for record in coll_procedure_risk.find({}, {"_id":0, "created_on": 0, "updated_on": 0, "release": 0, "version": 0}):
        # jai_record = {}
        # jai_record['procedure'] = record['Modality']
        # jai_record['pih_risk'] = record['PIH Risk (0-110)']
        # jai_record['pih_procedure_risk'] = record['PIH Risk (0-110)'] + client_score
        # jai_record['Frekles'] = record['Frekles (0-100)'] if jai_record['pih_procedure_risk']<=120 else 0
        # jai_record['LHR'] = 0 if data['sun_protection']=='No' else (record['LHR (0-100)'] if jai_record['pih_procedure_risk']<=120 else 0)
        # jai_record['cit_of_procedure'] = record['CIT Degree (15-100)'] if jai_record['pih_procedure_risk']<=120 else 0
        # if (hq == 25) & (retinol_adequate==15) & (sun_protection == 15):
        #     jai_record['Melasma'] = record['Melasma (0-75)'] if jai_record['pih_procedure_risk']<=120 else 0
        # else:
        #     jai_record['Melasma'] = False

        # print(record)

        jai_record = {}
        jai_record['procedure'] = record['Modality']
        jai_record['pih_risk'] = record['PIH Risk (0-110)'] if record['PIH Risk (0-110)']<=110 else False
        jai_record['pih_procedure_risk'] = record['PIH Risk (0-110)'] + client_score
        jai_record['pih_procedure_risk'] = jai_record['pih_procedure_risk'] if jai_record['pih_procedure_risk']<=120 else False

        jai_record['Frekles'] = record['Frekles (0-100)'] if jai_record['pih_procedure_risk']<=120 else 0
        jai_record['Frekles'] = jai_record['Frekles'] if ((jai_record['Frekles']<=100) & (jai_record['Frekles']>=25)) else False

        jai_record['LHR'] = 0 if data['sun_protection']=='No' else (record['LHR (0-100)'] if jai_record['pih_procedure_risk']<=120 else 0)
        jai_record['LHR'] = jai_record['LHR'] if (jai_record['LHR']>0) else False

        jai_record['cit_of_procedure'] = record['CIT Degree (15-100)'] if jai_record['pih_procedure_risk']<=120 else 0
        jai_record['cit_of_procedure'] = jai_record['cit_of_procedure'] if ((jai_record['cit_of_procedure']<=150) & (jai_record['cit_of_procedure']>=30)) else False
        for new_var in ['Down time',	'MDBTW',	'Treatment',	'Maintain',	'Rec in Summer' ]:
            jai_record[new_var] = record[new_var]
       

        if (hq == 25) & (retinol_adequate==15) & (sun_protection == 15):
            jai_record['Melasma'] = record['Melasma (0-75)'] if jai_record['pih_procedure_risk']<=120 else 0
        else:
            jai_record['Melasma'] = False        
        
        json_data.append(jai_record)
    import pandas as pd
    jai_data = pd.DataFrame.from_dict(json_data)
    jai_data = jai_data.loc[jai_data[key_dict[data['key']]] != False, :]
    json_data = jai_data.sort_values(by=[key_dict[data['key']]]).to_dict(orient='records')

    inputs = {}   
    print(data)
    print("\n")
    rem_cols = ['sun_sensitivity', 'retinol_adequate', 'retinol_inadequate', 'sun_protection', 'hq']
    for rem_col in rem_cols:
        inputs[rem_col] = data.pop(rem_col)
    

    if data['_is_new']:
        recos_data = {'client-score': client_score, 'inputs': [inputs], 'recos': json_data, 'created_at': data['updated_at']}
        data['recommended_data'] = {data['key']:[recos_data]}

        data.pop('key')
        coll_user_activities.insert_one(data)
    else:
        recos_data = {'client-score': client_score, 'inputs': [inputs], 'recos': json_data, 'created_at': data['updated_at']}
        data['recommended_data'] = prev_recos
        if data['key'] in data['recommended_data']:
            data['recommended_data'][data['key']].append(recos_data)
        else:
            data['recommended_data'].update({data['key']:[recos_data]})
        data.pop('key')
        coll_user_activities.update_one(filter={"_id": data['_id']}, update={'$set': data}, upsert=True)

    # "created_on": 0, "updated_on": 0, "release": 0, "version": 0, 'PIH & Procedure risk': 

    # Return a response (e.g., success message)
    return jsonify({'client-score': f"{client_score}", 'data': json_data})

# Company Names Endpoint
@app.route('/api/company')
def get_company_names():
    # Get the distinct company names
    company_names = coll_procedure_risk.distinct('Company')
    # Return the company names as a JSON response
    return jsonify(company_names)

# Select Machinery Endpoint
@app.route('/api/select-company')
def select_machinery():
    # Get the machinery type and plant name from the query parameters
    company_name = request.args.get('company_name')
    # plant_name = request.args.get('plant_name')
    # Find the machinery document with the specified machinery type and plant name in the database
    handpiece = coll_procedure_risk.distinct("Handpiece", {'Company': company_name})
    if handpiece:
        # If the machinery document is found, return a success message as a JSON response
        return jsonify({'message': f'Successfully selected {company_name}.', 'handpiece': handpiece})
    else:
        # If the machinery document is not found, return an error message as a JSON response with a 404 status code
        return jsonify({'error': f'Company not found for {company_name}.'}), 404      

# Select Machinery Endpoint
@app.route('/api/select-handpiece')
def select_machinery():
    # Get the machinery type and plant name from the query parameters
    company_name = request.args.get('company_name')
    handpiece = request.args.get('handpiece')
    # Find the machinery document with the specified machinery type and plant name in the database
    modality = coll_procedure_risk.distinct("Modality", {'Company': company_name, "Handpiece": handpiece})
    if modality:
        # If the machinery document is found, return a success message as a JSON response
        return jsonify({'message': f'Successfully selected Handpie: {company_name}.', 'handpiece': handpiece})
    else:
        # If the machinery document is not found, return an error message as a JSON response with a 404 status code
        return jsonify({'error': f'Company not found for {company_name}.'}), 404      

if __name__ == '__main__':
    app.secret_key = 'A1Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.run(host='0.0.0.0', port=8080, debug=True)
    client.close()
