# import streamlit as st
from datetime import datetime
import hashlib
import json
import re
import sys
import time

from bson import ObjectId
from dateutil.parser import parse

from medspa.constants import *
from medspa.exception import CustomException


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
    if not args:
        # Generate a random MongoDB ID based on the current time
        current_time = int(time.time())
        custom_id = ObjectId(str(current_time)[-10:] + '0000000000000000')
    else:
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
        self.phone_pattern = r'^\+\d{11,14}$'

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

    def is_valid_int(self, integer, max_limit, min_limit:int= 0):
        """
        Check if the given string is a valid integer between 0 and the specified limit.

        Args:
            integer (str): The string to check.
            min_limit (int): The lower limit for the integer.
            max_limit (int): The upper limit for the integer.

        Returns:
            bool: True if the string is a valid integer between 0 and the limit, False otherwise.

        Example:
            >>> self.is_valid_int('10', 100)
            True
            >>> self.is_valid_int('101', 100)
            False
        """
        if type(integer) == str:
            print(integer)
            return integer.isdigit() and min_limit <= int(integer) <= max_limit
        elif type(integer) in [int, float]:
            return min_limit <= int(integer) <= max_limit

    def raise_key_error(self, key):
        """
        Raise a key error with a default error message and a specified key.

        Args:
            key (str): The key that caused the error.

        Returns:
            tuple: A tuple containing the error message and the error code.

        Example:
            >>> self.raise_key_error('example_key')
            ({'status': 'error', 'responseMessage': 'Please fill mandatory fields', 'fields': 'example_key'}, 404)
        """
        default_message, error_key = {'status': 'error', "responseMessage": "Please fill mandatory fields", 'fields': key}, 404
        return default_message, error_key

    def raise_success_message(self):
        """
        Raise a success message with a default success message.

        Returns:
            tuple: A tuple containing the success message and the success code.

        Example:
            >>> self.raise_success_message()
            ({'status': 'success', 'responseMessage': 'Message as per action perform'}, 200)
        """
        return {'status': 'success', "responseMessage": "Message as per action perform"}, 200
    
    def raise_error_message(self, e):
        """
        Raise a error message with a default success message.

        Returns:
            tuple: A tuple containing the success message and the success code.

        Example:
            >>> self.raise_error_message()
            ({'status': 'error', "responseMessage": e}, 404)
        """
        return {'status': 'error', "responseMessage": e}, 404    

    def check_datatype_lead_status_template(self, record, collection_name, _is_insert:bool=True):
        capture_expected_format = coll_lead_format.find_one({"type": 'status'})
        del capture_expected_format['type']
        print(capture_expected_format)
        try:
            for key in record:
                if capture_expected_format[key] == 'is_valid_varchar':
                    a_length = 6 if key == 'label_color' else 255
                    if not self.is_valid_varchar(record[key], max_length=a_length):
                        return self.raise_key_error(key=key)
                    
                elif capture_expected_format[key] == 'is_valid_int':
                    if not self.is_valid_int(record[key], min_limit=1, max_limit=99):
                        return self.raise_key_error(key=key)
                    else:
                        record[key] = int(record[key])
                        
                elif capture_expected_format[key] == 'is_valid_phone':
                    if not self.is_valid_phone(record[key]):
                        return self.raise_key_error(key=key)
                    else:
                        record[key] = int(record[key])
                elif capture_expected_format[key] in coll_lead_format.distinct("_id"):
                    if not isinstance(record[key], ObjectId):
                        if not self.is_valid_object_id(record[key]):
                            return self.raise_key_error(key=key)
                        else:
                            record[key] = ObjectId(record[key])  
            
            if _is_insert: 
                    
                record['_id'], record['_is_new'] = mongo_id_generator(record['name'],
                                                                    collection_name=collection_name,
                                                                    variable='_id')

                count_collection_docs = collection_name.count_documents({})

                if count_collection_docs == 0:
                    record['_is_default'] = 1
                    record['priority'] = 1
                else:
                    record['_is_default'] = 0
                    record['priority'] = count_collection_docs + 1
                record['_is_deleted'] = 0

                record_content = collection_name.find_one({"_id": record["_id"]})

                if record_content is not None:
                    return self.raise_error_message(e="Status already exists")
                else:
                    record['created_on'] = datetime.now()
                    record['updated_on'] = record['created_on']
                    collection_name.insert_one(record)
                
                    return self.raise_success_message()
                
            else:
                
                record_content = collection_name.find_one(filter={"_id": record['_id']})

                if record_content is not None:
                    if 'name' in record:
                        if record['name'] != record_content['name']:
                            
                            record['_id'], record['_is_new'] = mongo_id_generator(record['name'],
                                                                                collection_name=collection_name,
                                                                                variable='_id')
                            coll_lead_status_database.delete_one(
                                filter={"_id": record_content['_id']}
                            )
                            coll_lead_status_database.update_one(
                                filter={"_id": record['_id']},
                                update={'$set': record},
                                upsert=True
                            )
                            
                    if 'priority' in record:
                        if record_content['priority'] == 1:
                            del record['priority'] # Cannot update the priority for p-1 record
                        elif (record['priority'] == 1) & (record_content['priority'] != 1):
                            # record['priority'] = record_content['priority']
                            del record['priority'] # Cannot update any other status priority to p-1 record
                        else:
                            if record['priority'] > record_content['priority']:
                                collection_name.update_many(
                                    {"priority": {"$gt": record_content['priority'], "$lte": record['priority']}},
                                    {"$inc": {"priority": -1}}
                                )
                            elif record['priority'] < record_content['priority']:
                                collection_name.update_many(
                                    {"priority": {"$gte": record['priority'], "$lt": record_content['priority']}},
                                    {"$inc": {"priority": 1}}
                                )

                    record['updated_on'] = datetime.now()
                    if record['name'] != record_content['name']:
                        for i in record_content:
                            if i not in record:
                                record[i] = record_content[i]
                        coll_lead_status_database.update_one(
                            filter={"_id": record['_id']},
                            update={'$set': record},
                            upsert=True
                        )
                        coll_lead_database.update_many(
                            {"status_id": record_content['_id']},
                            {"$set": {"status_id": record['_id']}}
                        )
                        coll_lead_status_database.delete_one(
                            filter={"_id": record_content['_id']}
                        )
                    else:
                        collection_name.update_one(
                            filter={"_id": record_content['_id']},
                            update={'$set': record}
                        )
                    return self.raise_success_message()

                else:
                    return self.raise_error_message(e="Status doesn't exists")
        
        except Exception as e:

            return self.raise_error_message(e=CustomException(e, sys))  
              
    def check_datatype_lead_template(self, record, collection_name, _is_insert:bool=True):
        """
        Checks the data type of each field in the record against the expected format
        and inserts or updates the record in the collection accordingly.

        Args:
            record (dict): The record to be inserted or updated
            collection_name (str): The name of the collection
            _is_insert (bool, optional): Whether to insert a new record (True) or update an existing one (False). Defaults to True.

        Returns:
            message (dict): A success or error message in dict eg. {'status': 'success', 'responseMessage': 'Message as per action perform'}
            key (int): Message key like 200, 404, etc

        Raises:
            Exception: If any error occurs during the process

        Example:
            >>> record = {
            ...     'first_name': 'John',
            ...     'last_name': 'Doe',
            ...     'email': 'johndoe@example.com',
            ...     'phone': '1234567890'
            ... }
            >>> collection_name = 'leads'
            >>> check_datatype_lead_template(record, collection_name)
            {'status': 'success', 'responseMessage': 'Message as per action perform'}, 200
        """
        try:
            capture_expected_format = coll_lead_format.find_one({"type": 'lead'})
            del capture_expected_format['type']
            
            print(capture_expected_format)  
                  
            for key in record:      
                if capture_expected_format[key] == 'is_valid_varchar': 
                         
                    if key in ['message']:
                        a_length=4294967295 # supporting longtext for names  
                    elif key=="country_code":
                        a_length=4 #
                    else:
                        a_length=255
                    
                    if not self.is_valid_varchar(record[key], max_length=a_length):
                        return self.raise_key_error(key=key)
                    
                elif capture_expected_format[key] == 'is_valid_email':
                    if not self.is_valid_email(record[key]):
                        return self.raise_key_error(key=key)
                
                elif capture_expected_format[key] == 'is_valid_int':
                    if not self.is_valid_int(record[key], min_limit=1000000000, max_limit=999999999999999):
                        
                        return self.raise_key_error(key=key)
                    else:
                        record[key] = int(record[key])

                elif capture_expected_format[key] in coll_lead_format.distinct("_id"):
                    if not isinstance(record[key], ObjectId):
                        if not self.is_valid_object_id(record[key]):
                            return self.raise_key_error(key=key)
                        else:
                            record[key] = ObjectId(record[key])
                                            
                # this code becomes redundant since phone number is processed in 2 parts country_code (varchar) + phone number (int)                                              
                elif capture_expected_format[key] == 'is_valid_phone':
                    if not self.is_valid_phone(record[key]):
                        return self.raise_key_error(key=key)
            
            if _is_insert: 
                  
                # record['_id'], record['_is_new'] = mongo_id_generator(record['first_name'], record['last_name'],
                #                                                       record['email'], record['phone'],
                #                                                       collection_name=collection_name,
                #                                                       variable='_id')
                
                record['status_id'] = coll_lead_status_database.find_one({'_is_default': 1})['_id']
                record['_is_deleted'] = 0

                # record_content = collection_name.find_one(filter={"_id": record['_id']})
                #
                # if record_content is not None:
                #     return jsonify({'status': 'error', "responseMessage": "User already exists"}), 404
                # else:
                #     record['created_on'] = datetime.now()
                #     record['updated_on'] = record['created_on']
                #     collection_name.insert_one(record)
                #     return jsonify({'status': 'success', "responseMessage": "Message as per action perform"}), 200   
                                         
                record['created_on'] = datetime.now()
                record['updated_on'] = record['created_on'] 
                print(record)               
                collection_name.insert_one(record)
                
                return self.raise_success_message()
                
            else:
                record['updated_on'] = datetime.now() 
                
                record_content = collection_name.find_one(filter={"_id": record['_id']})

                if record_content is not None:
                    record['updated_on'] = datetime.now()
                    collection_name.update_one(
                                filter={"_id": record['_id']},
                                update={'$set': record},
                                upsert=True
                    )
                    return self.raise_success_message()

                else:
                    return self.raise_error_message(e="User doesn't exists")
        
        except Exception as e:
            print(e)
            return self.raise_error_message(e=e)
     
    def check_datatype_email_template(self, record, collection_name, _is_insert:bool=True):
        """
        Check the data type of a record against an email template and insert it into a collection.

        Args:
            record (dict): The record to check.
            collection_name: The collection to insert the record into.
            _is_insert: To evaluate whether the record is supposed to be inserted or not

        Returns:
            tuple: A tuple containing the result message and the result code.

        Example:
            >>> record = {'example_key': 'example_value'}
            >>> collection_name = 'example_collection'
            >>> self.check_datatype_email_template(record, collection_name)
            ({'status': 'success', 'responseMessage': 'Message as per action perform'}, 200)
        """
        try:
            capture_expected_format = coll_lead_format.find_one({"type": 'email_template'})
            del capture_expected_format['type']
            print(capture_expected_format)

            for key in record:
                
                if capture_expected_format[key] == 'is_valid_varchar':
                    a_length = 4294967295 if key == 'html_code' else 255  # longtext length
                    if not self.is_valid_varchar(record[key], max_length=a_length):
                        return self.raise_key_error(key=key)

                elif capture_expected_format[key] == 'is_valid_int':
                    print(key)
                    if not self.is_valid_int(record[key], max_limit=1):
                        return self.raise_key_error(key=key)
                    else:
                        record[key] = int(record[key])
                        
                elif capture_expected_format[key] == 'is_valid_email':
                    if not self.is_valid_email(record[key]):
                        return self.raise_key_error(key=key)
                    
                elif capture_expected_format[key] in coll_lead_format.distinct("_id"):
                    if not isinstance(record[key], ObjectId):
                        if not self.is_valid_object_id(record[key]):
                            return self.raise_key_error(key=key)
                        else:
                            record[key] = ObjectId(record[key])
            
            if _is_insert:
                record['created_on'] = datetime.now()
                record['updated_on'] = record['created_on']                
                collection_name.insert_one(record)
                
            else:
                record['updated_on'] = datetime.now() 
                collection_name.update_one(
                            filter={"_id": record['_id']},
                            update={'$set': record},
                            upsert=True
                )
                        
            return self.raise_success_message()
        except Exception as e:
            print(e)
            return self.raise_error_message(e=e)