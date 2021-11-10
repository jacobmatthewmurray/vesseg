FROM python:3.8
RUN pip install rq docker
RUN mkdir /data 
COPY ./docker_launcher.py /app/docker_launcher/
COPY ./vesseg_logger.py /app/docker_launcher/
WORKDIR /app/docker_launcher
ENTRYPOINT ["rq", "worker"]