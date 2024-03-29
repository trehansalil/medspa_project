from gsheet import *

sheet_name = variable_extractor('sheet_name', var_type='string')

# url = f"{g_sheets_url}?sheetName={sheet_name}"
# # print(url)
# data = json.loads(requests.get(url).text)

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
elif sheet_name==sheet_name5:
    coll = db[sheet_name_equip_db_sheet]
    coll_backup = db_backup[sheet_name_equip_db_sheet]    

coll.drop()
coll_backup.drop()
coll_release_table.drop()

print(f"Dropped both the collections for data source: {sheet_name}")