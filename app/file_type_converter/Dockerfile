FROM ubuntu:18.04
RUN apt-get update && apt-get -y upgrade && apt-get -y install python3 python3-pip openjdk-11-jdk-headless locales

RUN locale-gen en_US.UTF-8 && pip3 install numpy && mkdir /data
ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8 JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64/

COPY ./file_type_converter/file_type_converter.py /app/file_type_converter/file_type_converter.py
COPY ./utils/vesseg_logger.py /app/utils/vesseg_logger.py 
WORKDIR /app/file_type_converter
RUN pip3 install javabridge==1.0.18 numpy==1.18.4 Pillow==7.1.2 python-bioformats==1.5.2

ENTRYPOINT [ "python3", "file_type_converter.py" ]