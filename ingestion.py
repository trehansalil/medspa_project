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
else:
    print('No Collection Created')

j = 1
import pymongo
max_release = None
for i in tqdm(data[:-1]):

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

            # if coll.count_documents({})>0:

                # if backup_coll:
                #     coll_backup.insert_many(coll.find())


                # i['release'] = max_release
                # i['version'] = max_version

                # if update_db:
                #     # updating records: new version, same release
                #     i['release'] = max_release
                #     i['version'] = max_version+1

                # else:
                #     # inserting new records: version = 1, new release
                #     i['release'] = max_release+1
                #     i['version'] = 1
                # coll.drop()                
                
            # else:
            #     i['release'] = 1
            #     i['version'] = 1

            coll.insert_one(i)
            j+=1
        else:
            # if max_release is not None:

            #     if update_db:
            #         # updating records: new version, same release
            #         i['release'] = max_release
            #         i['version'] = max_version+1

            #     else:
            #         # inserting new records: version = 1, new release
            #         i['release'] = max_release+1
            #         i['version'] = 1
            #     # coll.drop()                
                
            # else:
            #     i['release'] = 1
            #     i['version'] = 1
            coll.insert_one(i)
            j+=1

print(f"{sheet_name} data process is complete")