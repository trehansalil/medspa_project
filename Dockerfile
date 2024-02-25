FROM python:3:9-slim

WORKDIR ./

COPY . .

RUN pip install -r requirements.txt

CMD gunicorn --bind 0.0.0.0:8080 wsgi:app