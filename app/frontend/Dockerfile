FROM python:3.8-slim
COPY ./frontend/requirements.txt /frontend/requirements.txt
RUN pip install -r /frontend/requirements.txt && pip install gunicorn

RUN mkdir /data
COPY ./vesseg /frontend/vesseg
COPY ./config.py /frontend/config.py
WORKDIR /frontend
ENV FLASK_ENV=production
ENTRYPOINT ["gunicorn", "-b", ":8000", "--timeout", "300", "vesseg:create_app()"]

