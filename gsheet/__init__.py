import sys
import os
import re
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

clinic_database = config_parser.get('mongo_config', 'clinic_database')
clinic_equipment_database = config_parser.get('mongo_config', 'clinic_equipment_database')
mongo_db_user_activity_name = config_parser.get('mongo_config', 'mongo_db_user_activity_name')
mongo_db_coll_user = config_parser.get('mongo_config', 'mongo_db_coll_user')

mongo_db_coll_equipment_database = config_parser.get('mongo_config', 'mongo_db_coll_equipment_database')

mongo_db_lead_activity_name = config_parser.get('mongo_config', 'mongo_db_lead_activity_name')
lead_database = config_parser.get('mongo_config', 'lead_database')
lead_board_database = config_parser.get('mongo_config', 'lead_board_database')
lead_status_database = config_parser.get('mongo_config', 'lead_status_database')
lead_format = config_parser.get('mongo_config', 'lead_format')

# All file inputs
g_sheets_url = config_parser.get('input_files', 'g_sheets_url')
sheet_name1 = config_parser.get('input_files', 'sheet_name1')
sheet_name2 = config_parser.get('input_files', 'sheet_name2')
sheet_name3 = config_parser.get('input_files', 'sheet_name3')
sheet_name4 = config_parser.get('input_files', 'sheet_name4')
sheet_name5 = config_parser.get('input_files', 'sheet_name5')
sheet_name_equip_db_sheet = config_parser.get('input_files', 'sheet_name_equip_db_sheet')

client = MongoClient(mongo_db_uri)
db = client[mongo_db_name]
db_backup = client[mongo_db_backup_name]
db_user_activities = client[mongo_db_user_activity_name]
db_lead_activities = client[mongo_db_lead_activity_name]
coll_equipment_database = db[mongo_db_coll_equipment_database]

coll_procedure_risk = db[mongo_db_coll_procedure_risk]

coll_sun_sensitivity = db[mongo_db_coll_sun_sensitivity]
coll_hq = db[mongo_db_coll_hq]
coll_retinol = db[mongo_db_coll_retinol]
coll_sun_protection = db[mongo_db_coll_sun_protection]

coll_release_table = db[mongo_coll_release_table]
coll_release_table_backup = db_backup[mongo_coll_release_table]

coll_user_activities = db_user_activities[mongo_db_coll_user]
coll_clinic_database = db_user_activities[clinic_database]
coll_clinic_equipment_database = db_user_activities[clinic_equipment_database]

coll_lead_database = db_lead_activities[lead_database]
coll_lead_board_database = db_lead_activities[lead_board_database]
coll_lead_status_database = db_lead_activities[lead_status_database]
coll_lead_format = db_lead_activities[lead_format]


def variable_extractor(var_name='var1', var_type='string'):
    var = None
    for arg in sys.argv:
        if arg.startswith(f"{var_name}="):
            if var_type == 'string':
                var = arg.split("=")[1].strip()
            elif var_type == 'float':
                var = float(arg.split("=")[1].strip())
            elif var_type == 'datetime':
                var = parse(arg.split("=")[1].strip())
            elif var_type == 'array':
                var = arg.split("=")[1].strip()
                var = [i.strip() for i in var.split(',')]
            elif var_type == 'dict':
                var = arg.split("=")[1].strip()
                var = json.loads(var)
            elif var_type == 'bool':
                var = arg.split("=")[1].strip().lower()
                var = True if var == 'true' else (False if var == 'false' else None)
            else:
                var = int(arg.split("=")[1])

    if var is not None:
        print(f"{var_name} is:", var)
    else:
        print(f"{var_name} not provided/improper format")
    return var


def check_id(id, collection_name=coll_user_activities):
    sample_data = collection_name.find_one({"_id": id})
    if sample_data is None:
        return True, {}
    else:
        return False, sample_data['recommended_data']


def generate_custom_id(name, email, phone, collection_name=coll_user_activities):
    # Concatenate the name, email, and phone number into a single string
    phone = phone.replace(" ", "")
    name = name.lower().strip().replace("  ", " ")
    email = email.lower().strip()
    data_string = f"{name}{email}{phone}"

    # Hash the data string using the SHA256 algorithm
    sha256_hash = hashlib.sha256(data_string.encode()).hexdigest()

    # Take the first 12 bytes of the hash and convert it to a 24-character hexadecimal string

    custom_id = ObjectId(sha256_hash[:24])
    bool_exists, prev_recos = check_id(id=custom_id, collection_name=coll_user_activities)
    return custom_id, bool_exists, prev_recos


def _is_new_checker(id, collection_name, variable):
    sample_data = collection_name.find_one({variable: id})
    if sample_data is None:
        return True
    else:
        return False


def mongo_id_generator(*args, collection_name, variable='_id'):
    # Concatenate all the input arguments into a single string
    data_string = "".join(str(arg).lower().strip() for arg in args)

    # Hash the data string using the SHA256 algorithm
    sha256_hash = hashlib.sha256(data_string.encode()).hexdigest()

    # Take the first 12 bytes of the hash and convert it to a 24-character hexadecimal string
    custom_id = ObjectId(sha256_hash[:24])

    # Assuming check_id is a function that checks if the custom_id exists in the database
    _is_new_flag = _is_new_checker(id=custom_id, collection_name=collection_name, variable=variable)

    return custom_id, _is_new_flag


def remove_object_ids(record, cols):
    for key, value in record.items():
        if key in cols and isinstance(value, ObjectId):
            record[key] = str(value)  # Convert ObjectId to string
        elif isinstance(value, dict):
            remove_object_ids(value, cols)  # Recursive call for nested dictionaries
    return record


class DataValidator:
    def __init__(self):
        print(f"Initializing class name: {self.__class__.__name__}\n")

        # Regular expression for basic email validation
        self.email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

        # Ensure the name contains only letters
        self.name_pattern = "^[a-zA-Z]+$"

        # Define a regular expression pattern for a typical 10-digit phone number
        self.phone_pattern = r'^\d{10}$'

        # Define a regular expression pattern for varchar input (alphanumeric with spaces)
        self.varchar_pattern = r'^[a-zA-Z0-9_]+$'

    def is_valid_email(self, email):
        if email is None:
            return False  # None is not a valid email

        # Using re.match() to find a match between the regular expression and the email
        match = re.match(self.email_pattern, email.strip())  # Remove leading and trailing spaces

        # Return True if there is a match, otherwise return False
        return bool(match)

    def is_valid_varchar(self, varchar, max_length=255):
        if varchar is None:
            return False  # None is not a valid name

        return isinstance(varchar, str) and len(varchar) <= max_length  # Remove leading and trailing spaces

    def is_valid_phone(self, phone_number):
        if phone_number is None:
            return False  # None is not a valid phone number

        pattern = re.compile(self.phone_pattern)

        # Use the match() method to check if the phone number matches the pattern
        match = pattern.match(phone_number.strip())  # Remove leading and trailing spaces

        # Return True if the phone number is valid, False otherwise
        return bool(match)

    def is_valid_object_id(self, object_id):
        """
        Check if the given string is a valid MongoDB ObjectId.

        Args:
        object_id (str): The string to check.

        Returns:
        bool: True if the string is a valid MongoDB ObjectId, False otherwise.
        """
        # Regular expression to match a valid ObjectId
        pattern = re.compile(r'^[0-9a-fA-F]{24}$')
        return bool(pattern.match(object_id))

    def is_valid_int(self, integer, limit):
        """
        Check if the given string is a valid integer between 0 and the specified limit.

        Args:
        integer (str): The string to check.
        limit (int): The upper limit for the integer.

        Returns:
        bool: True if the string is a valid integer between 0 and the limit, False otherwise.
        """
        return integer.isdigit() and 0 <= int(integer) <= limit

