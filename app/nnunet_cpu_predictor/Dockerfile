FROM ubuntu:18.04
RUN apt-get update && apt-get -y upgrade && apt-get -y install python3 python3-pip locales
RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8
RUN pip3 install nnunet
RUN mkdir /nnUNet_raw_data_base /nnUNet_preprocessed /data
ENV nnUNet_raw_data_base="/nnUNet_raw_data_base" nnUNet_preprocessed="/nnUNet_preprocessed"
COPY ./nnunet_cpu_predictor/neural_network.py /usr/local/lib/python3.6/dist-packages/nnunet/network_architecture/neural_network.py
COPY ./nnunet_cpu_predictor/predict.py /usr/local/lib/python3.6/dist-packages/nnunet/inference/predict.py
COPY ./utils/vesseg_logger.py /usr/local/lib/python3.6/dist-packages/nnunet/inference/vesseg_logger.py
COPY ./nnunet_cpu_predictor/predict_from_png.py /app/nnunet_cpu_predictor/predict_from_png.py
WORKDIR /app/nnunet_cpu_predictor
ENTRYPOINT [ "python3", "predict_from_png.py" ]

