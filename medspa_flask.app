[Unit]
Description=Gunicorn instance to serve Flask app
After=network.target

[Service]
User=medspaa
Group=www-data
WorkingDirectory=/home/medspaa/repositories/medspa_project
Environment="PATH=/home/medspaa/repositiories/medspa_project/env/activate/bin"
ExecStart=/home/medspaa/repositories/medspa_project/env/bin/gunicorn --workers 3 --bind unix:peak.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target