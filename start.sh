pkill -f python
cd repositories/medspa_project && source env/bin/activate && git pull && gunicorn --bind 0.0.0.0:8080 wsgi:app > logs/app_run.log 2>&1&