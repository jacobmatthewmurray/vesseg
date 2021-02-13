FROM python:3.7-slim

RUN mkdir /vesseg_data /vesseg_models /vesseg_db
WORKDIR /vesseg_app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt && pip install gunicorn


COPY vesseg vesseg
COPY config.py .

ENV FLASK_ENV=production UPLOAD_PATH=/vesseg_data MODEL_PATH=/vesseg_models DB_PATH=/vesseg_db

ENTRYPOINT ["gunicorn", "-b", ":5555", "--access-logfile", "-", "--error-logfile", "-", "--timeout", "300", "vesseg:create_app()"]

