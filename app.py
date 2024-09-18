import subprocess
from datetime import datetime

from flask import Flask, request, jsonify, render_template

from gsheet import *
from medspa.exception import CustomException

app = Flask(__name__, static_folder=os.path.join(os.getcwd(), 'static'))

data_validator = DataValidator()


# Requires the PyMongo package.
# https://api.mongodb.com/python/current


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/add')
def add_numbers():
    x = int(request.args.get('x'))
    y = int(request.args.get('y'))
    z = x + y
    return jsonify({'result': z})


@app.route('/api/run_script', methods=['POST'])
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


@app.route('/api/submit', methods=['POST'])
def submit_form(collection_name=coll_clinic_equipment_database, source_collection_name=coll_procedure_risk,
                user_activities_collection_name=coll_user_activities):
    data = request.get_json()
    print(data)
    # Process the form data as needed

    data['tel'] = data['tel'].replace(" ", "").strip()
    data['name'] = data['name'].replace("  ", " ").strip().title()
    data['email'] = data['email'].lower().strip()

    data['_id'], data['_is_new'], prev_recos = generate_custom_id(name=data['name'], email=data['email'],
                                                                  phone=data['tel'])
    if data['_is_new']:
        data['created_at'] = datetime.now()
        data['updated_at'] = data['created_at']
    else:
        data['updated_at'] = datetime.now()

    sun_sensitivity = coll_sun_sensitivity.find_one({"Sun Sensitivity": data['sun_sensitivity']})['Values']
    retinol_adequate = coll_retinol.find_one({"Retinol": str(data['retinol_adequate']), "Category": "Adequate"})[
        'Values']
    print(retinol_adequate)
    retinol_inadequate = coll_retinol.find_one({"Retinol": str(data['retinol_inadequate']), "Category": "Inadequate"})[
        'Values']
    print(retinol_inadequate)
    sun_protection = coll_sun_protection.find_one({"Sun Protection": str(data['sun_protection'])})['Values']
    hq = coll_hq.find_one({"Hq 4%": data['hq']})['Values']
    # if data['sun']=='yes':
    #     sun_protection = 15
    # else:
    #     sun_protection = 0
    print(sun_sensitivity, retinol_adequate, retinol_inadequate, hq)

    if data['sun_sensitivity'] == "Dark Brown":
        client_score = sun_sensitivity - 0.3 * (sun_protection + retinol_adequate + retinol_inadequate + hq)
    elif data['sun_sensitivity'] == 'Black':
        client_score = sun_sensitivity - 0.5 * (sun_protection + retinol_adequate + retinol_inadequate + hq)
    else:
        client_score = sun_sensitivity - (sun_protection + retinol_adequate + retinol_inadequate + hq)
    client_score = client_score if client_score > 0 else 0

    data['latest_client_score'] = client_score

    json_data = []
    # if data['key'] == "Procedure" key = "procedure" elif data['key'] == 'PIH Risk' key = "pih_risk" elif data['key'] == 'PIH & Procedure Risk' key = "pih_procedure_risk" else 
    key_dict = {
        "procedure": 'procedure',
        "pih_risk": 'pih_risk',
        "pih_procedure_risk": 'pih_procedure_risk',
        "frekles": 'frekles',
        "lhr": 'lhr',
        "CIT of Procedure": 'cit_of_procedure',
        "Melasma": 'Melasma'
    }

    clinic_id = data['clinic_id']

    modality_list = collection_name.distinct("modality_id", {"clinic_id": ObjectId(clinic_id)})

    del data['clinic_id']

    filter = {
        'modality_id': {
            '$in': modality_list
        }
    }

    for record in source_collection_name.find(filter=filter,
                                              projection={"_id": 0, "created_on": 0, "updated_on": 0, "release": 0,
                                                          "version": 0}):

        record = {i: record[i] if str(record[i]).strip() != '' else 0 for i in record}

        jai_record = {}
        jai_record['procedure'] = record['Modality']
        jai_record['pih_risk'] = record['PIH Risk (0-110)'] if record['PIH Risk (0-110)'] <= 110 else False
        jai_record['pih_procedure_risk'] = record['PIH Risk (0-110)'] + client_score
        jai_record['pih_procedure_risk'] = jai_record['pih_procedure_risk'] if jai_record[
                                                                                   'pih_procedure_risk'] <= 120 else False

        jai_record['Frekles'] = record['Frekles (0-100)'] if jai_record['pih_procedure_risk'] <= 120 else 0
        jai_record['Frekles'] = jai_record['Frekles'] if (
                (jai_record['Frekles'] <= 100) & (jai_record['Frekles'] >= 25)) else False

        jai_record['LHR'] = 0 if data['sun_protection'] == 'No' else (
            record['LHR (0-100)'] if jai_record['pih_procedure_risk'] <= 120 else 0)
        jai_record['LHR'] = jai_record['LHR'] if (jai_record['LHR'] > 0) else False

        jai_record['cit_of_procedure'] = record['CIT Degree (15-100)'] if jai_record['pih_procedure_risk'] <= 120 else 0
        jai_record['cit_of_procedure'] = jai_record['cit_of_procedure'] if (
                (jai_record['cit_of_procedure'] <= 150) & (jai_record['cit_of_procedure'] >= 30)) else False
        for new_var in ['Down time', 'MDBTW', 'Treatment', 'Maintain', 'Rec in Summer']:
            jai_record[new_var.replace(" ", "_").lower()] = record[new_var]

        if (hq == 25) & (retinol_adequate == 15) & (sun_protection == 15):
            jai_record['Melasma'] = record['Melasma (0-75)'] if jai_record['pih_procedure_risk'] <= 120 else 0
        else:
            jai_record['Melasma'] = False

        json_data.append(jai_record)

    import pandas as pd
    jai_data = pd.DataFrame.from_dict(json_data)
    jai_data.columns = [i.lower().strip().replace(" ", "_") for i in jai_data.columns]
    print(jai_data.columns)
    jai_data = jai_data.loc[jai_data[data['key']] != False, :]
    json_data = jai_data.sort_values(by=[data['key']]).to_dict(orient='records')

    inputs = {}
    print(data)
    print("\n")
    rem_cols = ['sun_sensitivity', 'retinol_adequate', 'retinol_inadequate', 'sun_protection', 'hq']
    for rem_col in rem_cols:
        inputs[rem_col] = data.pop(rem_col)

    if data['_is_new']:
        recos_data = {'client-score': client_score, 'inputs': [inputs], 'recos': json_data,
                      'created_at': data['updated_at']}
        data['recommended_data'] = {data['key']: [recos_data]}

        data.pop('key')
        user_activities_collection_name.insert_one(data)
    else:
        recos_data = {'client-score': client_score, 'inputs': [inputs], 'recos': json_data,
                      'created_at': data['updated_at']}
        data['recommended_data'] = prev_recos
        if data['key'] in data['recommended_data']:
            data['recommended_data'][data['key']].append(recos_data)
        else:
            data['recommended_data'].update({data['key']: [recos_data]})
        data.pop('key')
        user_activities_collection_name.update_one(filter={"_id": data['_id']}, update={'$set': data}, upsert=True)

    # "created_on": 0, "updated_on": 0, "release": 0, "version": 0, 'PIH & Procedure risk': 

    # Return a response (e.g., success message)
    return jsonify({'client-score': f"{client_score}", 'data': json_data})


# Registration Endpoint
@app.route('/api/clinic_registration', methods=['POST'])
def do_registration(collection_name=coll_clinic_database):
    record = request.get_json()
    record['employee_type'] = "O"
    print(record)

    try:
        record = {i: record[i].strip() if type(record[i]) == str else record[i] for i in record}

        # Check if the username already exists in the database
        existing_username_user = collection_name.find_one({'username': record['username']})

        # Check if the username already exists in the database
        existing_email_user = collection_name.find_one({'email': record['email']})

        if (record['first_name'] in [None, ""]) | (record['last_name'] in [None, ""]) | (
                record['username'] in [None, ""]) | (record['email'] in [None, ""]) | (
                record['password'] in [None, ""]):
            return jsonify({'error': f'Sorry some error has occured please try again later'}), 404

        elif existing_username_user:
            return jsonify({'error': 'Username already exists'}), 400

        elif existing_email_user:
            return jsonify({'error': 'Email id already exists'}), 400

        record['_id'], record['_is_new'] = mongo_id_generator(record['email'], collection_name=collection_name,
                                                              variable='_id')
        record['created_on'] = datetime.now()
        record['updated_on'] = record['created_on']

        # _is_new_checker(id=username, collection_name=coll_user_activities, variable='username')
        # record['_is_username_new'] = _is_new_checker(id=username, collection_name=collection_name, variable='username')   

        print("\n")

        print(record)

        if record['_is_new']:
            collection_name.insert_one(record)
            return jsonify({'success': 'Registration Successful'}), 200
        else:
            return jsonify({'error': f'Sorry some error has occured please try again later'}), 404
        # Return the company names as a JSON response

    except Exception as e:
        print(e)
        return jsonify({'error': f'Sorry some error has occured please try again later'}), 404


# Registration Endpoint
@app.route('/api/login', methods=['POST'])
def do_login(collection_name=coll_clinic_database):
    record = request.get_json()
    print(record)
    try:

        if (record['username'] in [None, ""]) | (record['password'] in [None, ""]):
            # print(f"First error: {record['username']}")
            return jsonify({'error': f'Sorry some error has occured please try again later'}), 404

        # record['username'] = username
        # record['password'] = password

        record_content = collection_name.find_one(filter=record)
        # print(f"Second error: {record['username']}")
        # print(record_content)

        if record_content is None:
            return jsonify({'error': "User doesn't exists"}), 404
        else:
            record_content['clinic_id'] = str(record_content.pop('_id'))
            return jsonify({'success': 'User exists', "content": record_content}), 200
            # Return the company names as a JSON response

    except Exception as e:
        print(e)
        return jsonify({'error': f'Sorry some error has occured please try again later'}), 404

    # Company Names Endpoint


@app.route('/api/company')
def get_company_names(collection_name=coll_equipment_database):
    try:
        # Get the distinct company names
        company_names = collection_name.distinct('Company')
        # Return the company names as a JSON response
        return jsonify(company_names)
    except:
        return jsonify({'error': f'Sorry Data not found, Something went wrong'}), 404


# Select Machinery Endpoint
@app.route('/api/platform')
def select_platform(collection_name=coll_equipment_database):
    # Get the machinery type and plant name from the query parameters
    company_name = request.args.get('company_name')
    try:
        print("\n")
        print(company_name)
        # plant_name = request.args.get('plant_name')
        # Find the machinery document with the specified machinery type and plant name in the database
        print(company_name)
        platform = collection_name.distinct("Platform", {'Company': company_name})
        print(company_name)
        if platform != []:
            # If the machinery document is found, return a success message as a JSON response
            return jsonify({'success': f'Successfully identified list of platforms for company: {company_name}.',
                            'platform': platform})
        else:
            # If the machinery document is not found, return an error message as a JSON response with a 404 status code
            # return jsonify({'error': f'Platform not found for company: {company_name}.'}), 404 

            return jsonify({'error': f'Sorry Data not found, Something went wrong'}), 404
    except Exception as e:
        print(company_name, e)
        return jsonify({'error': f'Sorry Data not found, Something went wrong'}), 404


# Select Machinery Endpoint
@app.route('/api/handpiece')
def select_handpiece(collection_name=coll_equipment_database):
    try:
        # Get the machinery type and plant name from the query parameters
        company_name = request.args.get('company_name')
        platform = request.args.get('platform')
        # Find the machinery document with the specified machinery type and plant name in the database
        handpiece = collection_name.distinct("Handpiece", {'Company': company_name, "Platform": platform})
        if handpiece != []:
            # If the machinery document is found, return a success message as a JSON response
            return jsonify({
                'success': f'Successfully identified list of handpieces for company: {company_name}, platform: {platform}.',
                'handpiece': handpiece})
        else:
            # If the machinery document is not found, return an error message as a JSON response with a 404 status code
            # return jsonify({'error': f'Handpiece not found for company: {company_name}, platform: {platform}.'}), 404  
            return jsonify({'error': f'Sorry Data not found, Something went wrong'}), 404
    except:
        return jsonify({'error': f'Sorry Data not found, Something went wrong'}), 404


# Select Machinery Endpoint
@app.route('/api/modality')
def select_modality(collection_name=coll_equipment_database):
    try:
        # Get the machinery type and plant name from the query parameters
        company_name = request.args.get('company_name')
        platform = request.args.get('platform')
        handpiece = request.args.get('handpiece')
        # Find the machinery document with the specified machinery type and plant name in the database
        modality = collection_name.distinct("Modality",
                                            {'Company': company_name, "Platform": platform, "Handpiece": handpiece})
        if modality != []:
            # If the machinery document is found, return a success message as a JSON response
            return jsonify({
                'success': f'Successfully selected modality for company: {company_name}, platform: {platform} & handpiece: {handpiece}.',
                'modality': modality})
        else:
            # If the machinery document is not found, return an error message as a JSON response with a 404 status code
            # return jsonify({'error': f'Modality selection unsuccessful for company: {company_name}, platform: {platform} & handpiece: {handpiece}.'}), 404
            return jsonify({'error': f'Sorry Data not found, Something went wrong'}), 404
    except:
        return jsonify({'error': f'Sorry Data not found, Something went wrong'}), 404


# Select Submit Equipment Endpoint (clientwise)
@app.route('/api/submit_equipment', methods=['POST'])
def submit_modality(collection_name=coll_clinic_equipment_database):
    data = request.get_json()
    print(data)
    try:
        unwound_equipment_list = []
        count_ingest = 0
        for modality in data["modality"]:
            new_dict = {
                "clinic_id": ObjectId(data['clinic_id']),
                "Company": data["company_name"],
                "Platform": data["platform"],
                "Handpiece": data["handpiece"],
                "Modality": modality,
                "created_on": datetime.now(),
                "updated_on": datetime.now()
            }
            if collection_name.find_one(filter=new_dict) is None:

                if (new_dict['Company'] == '') & (new_dict['Platform'] == '') & (new_dict['Handpiece'] == '') & (
                        new_dict['Modality'] == ''):
                    continue
                else:
                    new_dict['equip_id'], new_dict['_is_new_equip'] = mongo_id_generator(new_dict['Company'],
                                                                                         new_dict['Platform'],
                                                                                         new_dict['Handpiece'],
                                                                                         new_dict['Modality'],
                                                                                         collection_name=collection_name,
                                                                                         variable='equip_id')
                    new_dict['modality_id'], new_dict['_is_new_modality'] = mongo_id_generator(new_dict['Company'],
                                                                                               new_dict['Handpiece'],
                                                                                               new_dict['Modality'],
                                                                                               collection_name=collection_name,
                                                                                               variable='modality_id')
                    new_dict['_id'], new_dict['_is_new_id'] = mongo_id_generator(new_dict['clinic_id'],
                                                                                 new_dict['Company'],
                                                                                 new_dict['Platform'],
                                                                                 new_dict['Handpiece'],
                                                                                 new_dict['Modality'],
                                                                                 collection_name=collection_name,
                                                                                 variable='_id')
                    if new_dict['_is_new_id']:
                        collection_name.insert_one(new_dict)
                        count_ingest += 1

                        unwound_equipment_list.append(new_dict)

        print(unwound_equipment_list)
        if count_ingest == 0:
            return jsonify({'error': f'Duplicate records'}), 200
        else:
            pre_existing_record_count = len(data["modality"]) - count_ingest
            return jsonify({'success': f'Inserted {count_ingest} Data points',
                            "pre_existing_record_count": pre_existing_record_count}), 200

    except:
        return jsonify({'error': f'Sorry Data not found, Something went wrong'}), 404


# Select Submit Equipment Endpoint (clientwise)
@app.route('/api/get_equipment', methods=['GET'])
def get_equipment(collection_name=coll_clinic_equipment_database):
    try:
        clinic_id = ObjectId(request.args.get('clinic_id'))
        print(clinic_id)
        filter = {"clinic_id": clinic_id}
        projection = {"_id": 0, "Company": 1, "Platform": 1, "Handpiece": 1, "Modality": 1, "equip_id": 1}

        if collection_name.find_one(filter=filter) is None:
            return jsonify({'error': f'No records for clinic_id: {str(clinic_id)}'}), 404
        else:
            print(collection_name.find_one(filter=filter, projection=projection))
            equipment_list = list(collection_name.find(filter=filter, projection=projection))
            for i in equipment_list:
                i['equip_id'] = str(i['equip_id'])
            return jsonify({'success': f'Fetched {len(equipment_list)} equipments for clinic_id: {str(clinic_id)}',
                            "content": equipment_list}), 200

    except:

        return jsonify({'error': f'Sorry Data not found, Something went wrong'}), 404

    # Select Delete Equipment Endpoint (clientwise)


@app.route('/api/delete_equipment', methods=['POST'])
def delete_equipment(collection_name=coll_clinic_equipment_database):
    data = request.get_json()
    try:
        clinic_id = ObjectId(data['clinic_id'])
        equip_id = ObjectId(data['equip_id'])
        # equip_id, _ = mongo_id_generator(data['Company'], data['Platform'], data['Handpiece'],	data['Modality'], collection_name=collection_name, variable='equip_id')

        filter = {"clinic_id": clinic_id, "equip_id": equip_id}
        # projection = {"_id": 0, "Company": 1, "Platform": 1, "Handpiece": 1, "Modality": 1}

        if collection_name.find_one(filter=filter) is None:
            return jsonify({'error': f'No records for clinic_id: {str(clinic_id)}, equip_id: {str(equip_id)}'}), 404
        else:
            print(collection_name.find_one(filter=filter))
            a = collection_name.delete_one(filter=filter)
            print(a)
            return jsonify({'success': f'Deleted equip_id: {str(equip_id)} for clinic_id: {str(clinic_id)}'}), 200

    except Exception as e:

        return jsonify({'error': f'Sorry unable to delete data, Something went wrong'}), 404


# Lead Capture Endpoint
@app.route('/api/lead/capture', methods=['POST'])
def lead_capture(collection_name=coll_lead_database):
    record = request.get_json()

    print(record)
    record_keys = ['first_name', 'last_name', "country_code", 'phone', 'email', 'message', 'source']
    other_keys = [i for i in record if i not in record_keys]
    missed_keys = [i for i in record_keys if i not in record.keys()]
    print(missed_keys)
    try:
        if len(other_keys) != 0:
            other_keys = ", ".join(other_keys)
            print(other_keys)
            return jsonify({'status': 'error', "responseMessage": "Please remove unnecessary fields",
                            'fields': other_keys}), 404
        elif len(missed_keys) != 0:
            missed_keys = ", ".join(missed_keys)
            print(missed_keys)
            return jsonify({'status': 'error', "responseMessage": "Please add missing fields",
                            'fields': missed_keys}), 404
        
        message, key = data_validator.check_datatype_lead_template(record=record, collection_name=collection_name, _is_insert=True)
        
        return jsonify(message), key

    except Exception as e:
        print(e)
        message, key = data_validator.raise_error_message(
            e=f"Sorry some error has occurred please try again later. Error: {e}"
        )
        
        return jsonify(message), key


# Lead List Endpoint
@app.route('/api/lead/list/<int:_is_deleted>', methods=['GET'])
def lead_list(_is_deleted, collection_name=coll_lead_database):
    try:
        records = [remove_object_ids(record=i, cols=['_id', 'status_id']) for i in
                   collection_name.find(filter={"_is_deleted": _is_deleted})]
        print(records)
        if len(records) != 0:
            return jsonify(
                {'status': 'success', "responseMessage": "Message as per action perform", 'data': records}), 200
        else:
            return jsonify({'status': 'error', "responseMessage": "No data found"}), 404

    except Exception as e:
        print(e)
        return jsonify({
            'status': 'error',
            "responseMessage": "Sorry, some error has occurred. Please try again later"
        }), 404


# Lead View Endpoint
@app.route('/api/lead/view/<string:_id>', methods=['GET'])
def lead_view(_id, collection_name=coll_lead_database):
    record = {}
    print(_id)
    try:
        record['_id'] = ObjectId(_id)
        record_content = collection_name.find_one(filter={"_id": record['_id']})

        if record_content is not None:

            record_content = remove_object_ids(record=record_content, cols=['_id', 'status_id'])

            return jsonify(
                {'status': 'success', "responseMessage": "Message as per action perform", 'data': record_content}), 200
        else:
            record['updated_on'] = record['created_on']
            return jsonify({'status': 'error', "responseMessage": "User doesn't exist"}), 404

    except Exception as e:
        print(e)
        return jsonify({
            'status': 'error',
            "responseMessage": "Sorry, some error has occurred. Please try again later"
        }), 404


# Lead Update Endpoint
@app.route('/api/lead/update', methods=['POST'])
def lead_update(collection_name=coll_lead_database, status_collection_name=coll_lead_status_database):
    record = request.get_json()

    print(record)
    # record_keys = ['first_name', 'last_name', 'phone', 'email', 'message', 'source']
    # other_keys = [i for i in record if i not in record_keys]
    # missed_keys = [i for i in record_keys if i not in record.keys()]
    # print(missed_keys)

    try:
        if 'status_id' in record:
            record['status_id'] = status_collection_name.find_one({'name': record['status_id']})['_id']
        if "_id" not in record:
            message, key = data_validator.raise_key_error(key='_id')
            return jsonify(message), key
        
        message, key = data_validator.check_datatype_lead_template(
            record=record, 
            collection_name=collection_name, 
            _is_insert=False
        )

        return jsonify(message), key
    
    except Exception as e:
        
        message, key = data_validator.raise_error_message(
            e=f"Sorry some error has occurred please try again later. Error: {e}"
        )
        
        return jsonify(message), key


@app.route('/api/lead/archive/<string:_id>', methods=['POST'])
def lead_archive(_id, collection_name=coll_lead_database):
    record = {}
    print(_id)
    try:
        record['_id'] = ObjectId(_id)
        record_content = collection_name.find_one(filter={"_id": record['_id']})

        if record_content is not None:
            record['_is_deleted'] = 1
            record['updated_on'] = datetime.now()
            collection_name.update_one(filter={"_id": record['_id']}, update={'$set': record})
            return jsonify({'status': 'success', "responseMessage": "Message as per action perform"}), 200
        else:
            record['updated_on'] = record['created_on']
            return jsonify({'status': 'error', "responseMessage": "User doesn't exist"}), 404

    except Exception as e:
        print(e)
        return jsonify({
            'status': 'error',
            "responseMessage": "Sorry, some error has occurred. Please try again later"
        }), 404


# Lead Restore Endpoint
@app.route('/api/lead/restore/<string:_id>', methods=['POST'])
def lead_restore(_id, collection_name=coll_lead_database):
    record = {}
    print(_id)
    try:
        record['_id'] = ObjectId(_id)
        record_content = collection_name.find_one(filter={"_id": record['_id']})

        if record_content is not None:
            record['_is_deleted'] = 0
            record['updated_on'] = datetime.now()
            collection_name.update_one(filter={"_id": record['_id']}, update={'$set': record})
            return jsonify({'status': 'success', "responseMessage": "Message as per action perform"}), 200
        else:
            record['updated_on'] = record['created_on']
            return jsonify({'status': 'error', "responseMessage": "User doesn't exist"}), 404

    except Exception as e:
        print(e)
        return jsonify({
            'status': 'error',
            "responseMessage": "Sorry, some error has occurred. Please try again later"
        }), 404


# Lead Delete Endpoint
@app.route('/api/lead/delete/<string:_id>', methods=['POST'])
def lead_delete(_id, collection_name=coll_lead_database):
    record = {}
    print(_id)
    try:
        record['_id'] = ObjectId(_id)
        record_content = collection_name.find_one(filter={"_id": record['_id']})

        if record_content is not None:
            collection_name.delete_one(filter={"_id": record['_id']})
            return jsonify({'status': 'success', "responseMessage": "Message as per action perform"}), 200
        else:
            record['updated_on'] = record['created_on']
            return jsonify({'status': 'error', "responseMessage": "User doesn't exist"}), 404

    except Exception as e:
        print(e)
        return jsonify({
            'status': 'error',
            "responseMessage": "Sorry, some error has occurred. Please try again later"
        }), 404


# Leadboard Status Add Endpoint
@app.route('/api/leadboard/status/add', methods=['POST'])
def leadboard_status_add(collection_name=coll_lead_status_database):
    record = request.get_json()

    print(record)
    record_keys = ['name', 'label_color']
    other_keys = [i for i in record if i not in record_keys]
    missed_keys = [i for i in record_keys if i not in record.keys()]

    try:
        if len(other_keys) != 0:
            other_keys = ", ".join(other_keys)
            print(other_keys)
            return jsonify({'status': 'error', "responseMessage": "Please remove unnecessary fields",
                            'fields': other_keys}), 404
        elif len(missed_keys) != 0:
            missed_keys = ", ".join(missed_keys)
            print(missed_keys)
            return jsonify({'status': 'error', "responseMessage": "Please add missing fields",
                            'fields': missed_keys}), 404

        message, key = data_validator.check_datatype_lead_status_template(record=record, collection_name=collection_name, _is_insert=True)

        
    
    except Exception as e:
        print(e)
        message, key = data_validator.raise_error_message(e=e)
        # return jsonify(
        #     {'status': 'error', "responseMessage": "Sorry some error has occurred please try again later"}), 404
        
    return jsonify(message), key


# Leadboard Status List Endpoint
@app.route('/api/leadboard/status/list', methods=['GET'])
def leadboard_status_list(collection_name=coll_lead_status_database):
    try:
        records = [remove_object_ids(record=i, cols=['_id', 'status_id']) for i in
                   collection_name.find()]
        print(records)
        if len(records) != 0:
            return jsonify(
                {'status': 'success', "responseMessage": "Message as per action perform", 'data': records}), 200
        else:
            return jsonify({'status': 'error', "responseMessage": "No data found"}), 404

    except Exception as e:
        print(e)
        return jsonify({
            'status': 'error',
            "responseMessage": "Sorry, some error has occurred. Please try again later"
        }), 404


# Leadboard Status Edit Endpoint
@app.route('/api/leadboard/status/edit/<string:_id>', methods=['GET'])
def leadboard_status_edit(_id, collection_name=coll_lead_status_database):
    record = {}
    print(_id)
    try:
        record['_id'] = ObjectId(_id)
        record_content = collection_name.find_one(filter={"_id": record['_id']})

        if record_content is not None:

            record_content = remove_object_ids(record=record_content, cols=['_id'])

            return jsonify(
                {'status': 'success', "responseMessage": "Message as per action perform", 'data': record_content}), 200
        else:
            record['updated_on'] = record['created_on']
            return jsonify({'status': 'error', "responseMessage": "Status doesn't exist"}), 404

    except Exception as e:
        print(e)
        return jsonify({
            'status': 'error',
            "responseMessage": "Sorry, some error has occurred. Please try again later"
        }), 404


# Leadboard Status Update Endpoint
@app.route('/api/leadboard/status/update', methods=['POST'])
def leadboard_status_update(collection_name=coll_lead_status_database, lead_database=coll_lead_database):
    record = request.get_json()
    record['_id'] = ObjectId(record['_id'])

    print(record)

    try:
        if "_id" not in record:
            message, key = data_validator.raise_key_error(key="_id")
            return jsonify(message), key

        message, key = data_validator.check_datatype_lead_status_template(record=record, collection_name=collection_name, _is_insert=False)

        return jsonify(message), key
    
    except Exception as e:
        raise CustomException(e, sys) from e
        # print(e)
        # return jsonify(
        #     {'status': 'error', "responseMessage": "Sorry some error has occurred please try again later"}), 404


# Leadboard Status Delete Endpoint
@app.route('/api/leadboard/status/delete/<string:_id>', methods=['POST'])
def leadboard_status_delete(_id, collection_name=coll_lead_status_database):
    record = {}
    print(_id)
    try:
        record['_id'] = ObjectId(_id)
        record_content = collection_name.find_one(filter={"_id": record['_id']})

        if record_content is not None:
            if record_content['priority'] == 1:
                message, key = data_validator.raise_error_message(e="Status with Priority 1 cannot be deleted")
            else:
          
                collection_name.delete_one(filter={"_id": record['_id']}) # delete this first 
                
                # fetching predessor id
                new_status_id = collection_name.find_one({"priority": record_content["priority"] - 1})['_id']
                
                # replacing all leads with this predesessor id
                coll_lead_database.update_many(
                   {'status_id': record['_id']},
                   {'$set': {'status_id': new_status_id}}
                )
                
                # now update all priority above record_content['priority'] by decrease of -1
                collection_name.update_many(
                    {"priority": {"$gte": record_content['priority']}},
                    {"$inc": {"priority": -1}}
                )  
                message, key = data_validator.raise_success_message()    
        else:
            record['updated_on'] = record['created_on']
            message, key = data_validator.raise_error_message(e="Status doesn't exists")

    except Exception as e:
        message, key = data_validator.raise_error_message(e=e)
    
    return jsonify(message), key


# Email Template Add Endpoint
@app.route('/api/email_template/add', methods=['POST'])
def email_template_add(collection_name=coll_email_template_database):
    
    record = request.get_json()

    print(record)
    record_keys = ['title', 'html_code', 'status']
    other_keys = [i for i in record if i not in record_keys]
    missed_keys = [i for i in record_keys if i not in record.keys()]

    try:
        if len(other_keys) != 0:
            other_keys = ", ".join(other_keys)
            print(other_keys)
            return jsonify({'status': 'error', "responseMessage": "Please remove unnecessary fields",
                            'fields': other_keys}), 404
        elif len(missed_keys) != 0:
            missed_keys = ", ".join(missed_keys)
            print(missed_keys)
            return jsonify({'status': 'error', "responseMessage": "Please add missing fields",
                            'fields': missed_keys}), 404

        message, key = data_validator.check_datatype_email_template(record=record, collection_name=collection_name)
        
        return jsonify(message), key

    except Exception as e:
        print(e)
        return jsonify(
            {'status': 'error', "responseMessage": "Sorry some error has occurred please try again later"}), 404


# Email Template List Endpoint
@app.route('/api/email_template/list', methods=['GET'])
def email_template_list(collection_name=coll_email_template_database):
    try:
        records = [remove_object_ids(record=i, cols=['_id']) for i in
                   collection_name.find()]
        print(records)
        if len(records) != 0:
            return jsonify(
                {'status': 'success', "responseMessage": "Message as per action perform", 'data': records}), 200
        else:
            return jsonify({'status': 'error', "responseMessage": "No data found"}), 404

    except Exception as e:
        print(e)
        return jsonify({
            'status': 'error',
            "responseMessage": "Sorry, some error has occurred. Please try again later"
        }), 404


# Email Template Edit Endpoint
@app.route('/api/email_template/edit/<string:_id>', methods=['GET'])
def email_template_edit(_id, collection_name=coll_email_template_database):
    record = {}
    print(_id)
    try:
        record['_id'] = ObjectId(_id)
        record_content = collection_name.find_one(filter={"_id": record['_id']})

        if record_content is not None:

            record_content = remove_object_ids(record=record_content, cols=['_id'])

            return jsonify(
                {'status': 'success', "responseMessage": "Message as per action perform", 'data': record_content}), 200
        else:
            record['updated_on'] = record['created_on']
            return jsonify({'status': 'error', "responseMessage": "Status doesn't exist"}), 404

    except Exception as e:
        print(e)
        return jsonify({
            'status': 'error',
            "responseMessage": "Sorry, some error has occurred. Please try again later"
        }), 404

# Email Template Update Endpoint
@app.route('/api/email_template/update', methods=['POST'])
def email_template_update(collection_name=coll_email_template_database):
    record = request.get_json()
    record['_id'] = ObjectId(record['_id'])

    print(record)

    try:
        if "_id" not in record:
            return jsonify(
                {'status': 'error', "responseMessage": "Please fill mandatory fields", 'fields': "_id"}), 404
        
        message, key = data_validator.check_datatype_email_template(record=record, collection_name=collection_name, _is_insert=False)
        return jsonify(message), key
    
    except Exception as e:
        print(e)
        return jsonify({
            'status': 'error',
            "responseMessage": "Sorry, some error has occurred. Please try again later"
        }), 404        

# Email Template Delete Endpoint
@app.route('/api/email_template/delete/<string:_id>', methods=['POST'])
def email_template_delete(_id, collection_name=coll_email_template_database):
    record = {}
    print(_id)
    try:
        record['_id'] = ObjectId(_id)
        record_content = collection_name.find_one(filter={"_id": record['_id']})

        if record_content is not None:
            collection_name.delete_one(filter={"_id": record['_id']})
            return jsonify({'status': 'success', "responseMessage": "Message as per action perform"}), 200
        else:
            record['updated_on'] = record['created_on']
            return jsonify({'status': 'error', "responseMessage": "Status doesn't exist"}), 404

    except Exception as e:
        print(e)
        return jsonify({
            'status': 'error',
            "responseMessage": "Sorry, some error has occurred. Please try again later"
        }), 404


if __name__ == '__main__':
    app.secret_key = 'A1Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.run(host='0.0.0.0', port=8080, debug=True)
    client.close()
