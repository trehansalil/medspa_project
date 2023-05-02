git config --global user.name "Salil Trehan"
git config --global user.email "trehansalil1@gmail.com"
source env/bin/activate
pip install -r requirements.txt > logs/requirements.log 2>&1&

#!/bin/bash

python drop_coll.py sheet_name=procedure_risk > logs/drop_procedure_risk_ingestion.log 2>&1&
python drop_coll.py sheet_name=sun_sensitivity > logs/drop_sun_sensitivity_ingestion.log 2>&1&
python drop_coll.py sheet_name=hq > logs/drop_hq_ingestion.log 2>&1&
python drop_coll.py sheet_name=retinol > logs/drop_retinol_ingestion.log 2>&1&  
