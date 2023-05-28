#!/bin/bash

git config --global user.name "Salil Trehan"
git config --global user.email "trehansalil1@gmail.com"
source env/bin/activate
pip install -r requirements.txt > logs/requirements.log 2>&1&

# Check if the input parameter is 1, 0, true, or false
if [[ "$1" =~ ^(1|0|true|false)$ ]]; then
  # Run the Python script and pass the input parameter
    echo "Valid input."
    #  2>&1&
    python update.py update_db="$1"> logs/update.log
    python ingestion.py sheet_name=sun_sensitivity update_db="$1" > logs/sun_sensitivity_ingestion.log 2>&1&
    python ingestion.py sheet_name=hq update_db="$1"> logs/hq_ingestion.log 2>&1&
    python ingestion.py sheet_name=retinol update_db="$1"> logs/retinol_ingestion.log 2>&1&
    python ingestion.py sheet_name=sun_protection update_db="$1"> logs/sun_protection.log 2>&1&
    python ingestion.py sheet_name=procedure_risk update_db="$1"> logs/procedure_risk_ingestion.log
    
else
  echo "Invalid input. Please provide either 1, 0, true, or false."
  exit 1
fi

