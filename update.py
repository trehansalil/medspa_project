from gsheet import *
import pymongo

max_release = coll_release_table.find_one(sort=[("release", pymongo.DESCENDING)])['release']
max_version = coll_release_table.find_one(sort=[("version", pymongo.DESCENDING)])['version']
update_db = variable_extractor('update_db', var_type='bool')