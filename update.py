from gsheet import *
import pymongo
from datetime import datetime

update_db = variable_extractor('update_db', var_type='bool')

i = {'release': 1, 'version': 1, 'comments': "This is the preliminary version for our application", 'inserted_at': datetime.now(), 'updated_at': datetime.now()}

if coll_release_table.count_documents({})>0:

    max_release = coll_release_table.find_one(sort=[("release", pymongo.DESCENDING)])['release']
    max_version = coll_release_table.find_one(sort=[("release", pymongo.DESCENDING), ("version", pymongo.DESCENDING)])['version']
    
    if update_db:
        # updating records: new version, same release
        i['release'] = max_release
        i['version'] = max_version+1

    else:
        # inserting new records: version = 1, new release
        i['release'] = max_release+1
        i['version'] = 1
        # coll_release_table_backup.insert_many(coll_release_table.find_one())

coll_release_table.update_one({'release': i['release'], 'version': i['version']}, {'$set': i}, upsert=True)