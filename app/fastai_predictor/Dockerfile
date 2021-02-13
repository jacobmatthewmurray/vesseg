FROM ubuntu:20.04
RUN apt-get update && apt-get -y upgrade && apt-get -y install cmake locales && locale-gen en_US.UTF-8 && apt-get install -y python3 python3-pip
ENV LANG en_US.UTF-8 LANGUAGE en_US:en LC_ALL en_US.UTF-8
RUN pip3 install numpy fastai==1.0.61
RUN mkdir /data 
COPY ./utils /app/utils
COPY ./fastai_predictor/fastai_predictor.py /app/fastai_predictor/
WORKDIR /app/fastai_predictor
ENTRYPOINT ["python3", "fastai_predictor.py"]