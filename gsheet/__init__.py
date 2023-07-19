import sys
import os
# import streamlit as st
import configparser
import json
import hashlib
from bson import ObjectId

from dateutil.parser import parse
from pymongo import MongoClient


config_path = os.path.join(os.getcwd(), "config_file.config")

config_parser = configparser.ConfigParser()
config_parser.read(config_path)

# All DB Inputs
mongo_db_uri = config_parser.get('mongo_config', 'mongo_db_uri')
mongo_db_name = config_parser.get('mongo_config', 'mongo_db_name')
mongo_db_backup_name = config_parser.get('mongo_config', 'mongo_db_backup_name')
mongo_db_coll_procedure_risk = config_parser.get('mongo_config', 'mongo_db_coll_procedure_risk')
mongo_db_coll_sun_sensitivity = config_parser.get('mongo_config', 'mongo_db_coll_sun_sensitivity')
mongo_db_coll_hq = config_parser.get('mongo_config', 'mongo_db_coll_hq')
mongo_db_coll_retinol = config_parser.get('mongo_config', 'mongo_db_coll_retinol')
mongo_db_coll_sun_protection = config_parser.get('mongo_config', 'mongo_db_coll_sun_protection')
mongo_coll_release_table = config_parser.get('mongo_config', 'mongo_coll_release_table')
backup_coll = config_parser.getboolean('mongo_config', 'backup_coll')

mongo_db_user_activity_name = config_parser.get('mongo_config', 'mongo_db_user_activity_name')
mongo_db_coll_user = config_parser.get('mongo_config', 'mongo_db_coll_user')

# All file inputs
g_sheets_url = config_parser.get('input_files', 'g_sheets_url')
sheet_name1 = config_parser.get('input_files', 'sheet_name1')
sheet_name2 = config_parser.get('input_files', 'sheet_name2')
sheet_name3 = config_parser.get('input_files', 'sheet_name3')
sheet_name4 = config_parser.get('input_files', 'sheet_name4')
sheet_name5 = config_parser.get('input_files', 'sheet_name5')

client = MongoClient(mongo_db_uri)
db = client[mongo_db_name]
db_backup = client[mongo_db_backup_name]
db_user_activities = client[mongo_db_user_activity_name]

coll_release_table = db[mongo_coll_release_table]
coll_release_table_backup = db_backup[mongo_coll_release_table]

coll_user_activities = db_user_activities[mongo_db_coll_user]

def variable_extractor(var_name='var1', var_type='string'):
    var = None
    for arg in sys.argv:
        if arg.startswith(f"{var_name}="):
            if var_type=='string':
                var = arg.split("=")[1].strip()
            elif var_type=='float':
                var = float(arg.split("=")[1].strip())
            elif var_type=='datetime':
                var = parse(arg.split("=")[1].strip())
            elif var_type=='array':
                var = arg.split("=")[1].strip()
                var = [i.strip() for i in var.split(',')]
            elif var_type=='dict':
                var = arg.split("=")[1].strip()
                var = json.loads(var)
            elif var_type=='bool':
                var = arg.split("=")[1].strip().lower()
                var = True if var=='true' else (False if var=='false' else None)
            else:
                var = int(arg.split("=")[1])

    if var is not None:
        print(f"{var_name} is:", var)
    else:
        print(f"{var_name} not provided/improper format")
    return var


def check_id(id):

    sample_data = coll_user_activities.find_one({"_id": id})
    if sample_data is None:
        return True, {}
    else:
        return False, sample_data['recommended_data']
    
def generate_custom_id(name, email, phone):
    # Concatenate the name, email, and phone number into a single string
    phone = phone.replace(" ", "")
    name = name.lower().strip().replace("  ", " ")
    email = email.lower().strip()
    data_string = f"{name}{email}{phone}"

    # Hash the data string using the SHA256 algorithm
    sha256_hash = hashlib.sha256(data_string.encode()).hexdigest()

    # Take the first 12 bytes of the hash and convert it to a 24-character hexadecimal string

    custom_id = ObjectId(sha256_hash[:24])
    bool_exists, prev_recos = check_id(custom_id)
    return custom_id, bool_exists, prev_recos



# # Example usage:
# name = "John Doe"
# email = "johndoe@example.com"
# phone = "1234567890"

# custom_id = generate_custom_id(name, email, phone)
# print(custom_id)
