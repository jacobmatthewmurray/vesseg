#!/usr/bin/env python3

import os
import docker
import rq
import argparse
import json
import time
import inspect
from rq import get_current_job
from vesseg_logger import VessegLogger


def validate_redis_status(log: dict) -> bool:
    c1 = True if log.get('log_type') == 'status' else False
    c2 = True if log.get('message') else False
    try:
        c3 = 0<= float(log.get('message')) <= 1
    except:
        c3 = False 
    return c1==c2==c3==True   


def docker_launcher(container_name, data_directory, commands, redis=True): 
    """ Launches docker container.
    """

    vl = VessegLogger()
    vl.update_log({'executing_redis_job': get_current_job().get_id() if redis else None})
    vl.update_log({'container': container_name})

    bindings = {data_directory : {'bind': '/data', 'mode': 'rw'}}
    volumes = list(bindings.keys())
    client = docker.APIClient()
    host_config = client.create_host_config(binds=bindings)
    container = client.create_container(image=container_name, volumes=volumes, host_config=host_config, command=commands)
    container_id = container.get('Id')
    client.start(container=container_id)
    output = client.attach(container=container_id, stream=True)

    for line in output:

        log = vl.d2p(line)

        if redis and validate_redis_status(log):
            try: 
                job = get_current_job()
                job.meta['status'] = float(log.get('message'))
                job.save_meta()
            except Exception as e:
                print(e, flush=True) 


# if __name__ == "__main__":

#     # For testing of the file type converter
#     container_name = 'processor:latest'
#     data_directory = '/Users/jacobmurray/projects/vesseg/data/'
#     commands = ['-i', '/data/projects/1/raw/pil/png', '-o', '/data/projects/1/preprocessed', '-f', 'resize']
    
#     # For testing of the nnunet_cpu_predictor
#     # container_name = 'nnunet_cpu_predictor:latest'
#     # data_directory = '/Users/jacobmurray/projects/vesseg/data/'
#     # commands = ['-i', '/data/projects/1/preprocessed', '-o', '/data/projects/1/predicted/nnunet_112/masks', '-m', '/data/models/nnUNet_trained_models', '-t', '112']
    
# #     # For testing of the fastai_predictor
# #     container_name = 'fastai_predictor:latest'
# #     data_directory = '/Users/jacobmurray/projects/vesseg/data/'
# #     commands = ['-i', '/data/projects/1/preprocessed', '-o', '/data/projects/1/predicted/fastai_01/masks', '-m', '/data/models/fastai_01']

# #     # For testing of the prepostprocessor
#     # container_name = 'processor:latest'
#     # data_directory = '/Users/jacobmurray/projects/vesseg/data/'
#     # db = "sqlite:////Users/jacobmurray/projects/vesseg/data/db/vesseg.db"
#     # commands = ['-f', 'analyzer', '-i', '/data/projects/1', '-o', '', '-k', '{"project_id": "1", "predictionmodel_id": "1", "predictionmodel_name": "fastai_01"}']

#     docker_launcher(container_name, data_directory, commands, redis=False)

# #     # For testing as a worker
# #     # docker run -v /var/run/docker.sock:/var/run/docker.sock docker_launcher:latest -u redis://host.docker.internal:6379/0 vesseg


