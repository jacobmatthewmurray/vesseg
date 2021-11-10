FROM python:3.8
RUN pip install pandas
RUN mkdir /cmi
COPY ./combine_meta_info.py /cmi/combine_meta_info.py
WORKDIR /cmi
ENTRYPOINT ["python3", "combine_meta_info.py"]