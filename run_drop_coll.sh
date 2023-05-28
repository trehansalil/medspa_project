git config --global user.name "Salil Trehan"
git config --global user.email "trehansalil1@gmail.com"
source env/bin/activate
pip install -r requirements.txt > logs/requirements.log 2>&1&

#!/bin/bash

python drop_coll.py sheet_name=procedure_risk > logs/procedure_risk_drop.log 2>&1&
python drop_coll.py sheet_name=sun_sensitivity > logs/sun_sensitivity_drop.log 2>&1&
python drop_coll.py sheet_name=hq > logs/hq_drop.log 2>&1&
python drop_coll.py sheet_name=retinol > logs/retinol_drop.log 2>&1&  
python drop_coll.py sheet_name=sun_protection > logs/sun_protection_drop.log 2>&1&
