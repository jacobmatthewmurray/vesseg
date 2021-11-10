FROM python:3.8
RUN pip install matplotlib Pillow numpy pandas
RUN mkdir /data 
COPY ./processor.py /app/processor/
WORKDIR /app/processor
ENTRYPOINT ["python3", "processor.py"]