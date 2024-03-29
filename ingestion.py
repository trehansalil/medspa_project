import requests
import sys
import configparser
from tqdm import tqdm
from datetime import datetime
import json

from gsheet import *

sheet_name = variable_extractor('sheet_name', var_type='string')
update_db = variable_extractor('update_db', var_type='bool')

url = f"{g_sheets_url}?sheetName={sheet_name}"
# print(url)
data = json.loads(requests.get(url).text)

if sheet_name==sheet_name1:
    coll = db[mongo_db_coll_procedure_risk]
    coll_backup = db_backup[mongo_db_coll_procedure_risk]
elif sheet_name==sheet_name2:
    coll = db[mongo_db_coll_sun_sensitivity]
    coll_backup = db_backup[mongo_db_coll_sun_sensitivity]
elif sheet_name==sheet_name3:
    coll = db[mongo_db_coll_hq]
    coll_backup = db_backup[mongo_db_coll_hq]
elif sheet_name==sheet_name4:
    coll = db[mongo_db_coll_retinol]
    coll_backup = db_backup[mongo_db_coll_retinol]
elif sheet_name==sheet_name5:
    coll = db[mongo_db_coll_sun_protection]
    coll_backup = db_backup[mongo_db_coll_sun_protection]   
elif sheet_name==sheet_name_equip_db_sheet:
    coll = db[mongo_db_coll_equipment_database]
    coll_backup = db_backup[mongo_db_coll_equipment_database]
else:
    print('No Collection Created')

j = 1
import pymongo
max_release = None
for i in tqdm(data[:-1]):
    i = {j: i[j].strip() for j in i}
    if sheet_name==sheet_name_equip_db_sheet:
        if (i['Company']=='') & (i['Platform']=='') & (i['Handpiece']=='') & (i['Modality']==''):
            continue
        else:
            i['equip_id'], i['_is_new_equip'] = mongo_id_generator(i['Company'], i['Platform'], i['Handpiece'],	i['Modality'], collection_name=coll, variable='equip_id')
            i['modality_id'], i['_is_new_modality'] = mongo_id_generator(i['Company'], i['Handpiece'],	i['Modality'], collection_name=coll, variable='modality_id')
    elif sheet_name==sheet_name1:
        if (i['Company']=='') & (i['Handpiece']=='') & (i['Modality']==''):
            continue
        else:       
            i['modality_id'], i['_is_new_modality'] = mongo_id_generator(i['Company'], i['Handpiece'],	i['Modality'], collection_name=coll, variable='modality_id')        
    i['created_on'] = datetime.now()
    i['updated_on'] = datetime.now()

    max_release = coll_release_table.find_one(sort=[("release", pymongo.DESCENDING)])['release']
    max_version = coll_release_table.find_one(sort=[("release", pymongo.DESCENDING), ("version", pymongo.DESCENDING)])['version']
    print(max_release, max_version)
    i['release'] = max_release
    i['version'] = max_version   
    if 'coll' in locals():
        # print(i)
        if j==1:
            if coll.count_documents({})>0:
                if backup_coll:
                    coll_backup.insert_many(coll.find())

            coll.drop()
            
            coll.insert_one(i)
            j+=1
        else:
            coll.insert_one(i)
            j+=1

print(f"{sheet_name} data process is complete")