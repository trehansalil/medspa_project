import configparser
import os

from pymongo import MongoClient

config_path = os.path.join(os.getcwd(), "config_file.config")

config_parser = configparser.ConfigParser()
config_parser.read(config_path)

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
email_template_database = config_parser.get('mongo_config', 'email_template_database')
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
coll_email_template_database = db_lead_activities[email_template_database]
coll_lead_format = db_lead_activities[lead_format]
