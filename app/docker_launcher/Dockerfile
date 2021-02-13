FROM python:3.8
RUN pip install rq docker
RUN mkdir /data 
COPY ./utils /app/utils
COPY ./docker_launcher/docker_launcher.py /app/docker_launcher/
WORKDIR /app/docker_launcher
ENTRYPOINT ["rq", "worker"]