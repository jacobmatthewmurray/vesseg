#!/usr/bin/env python3

"""
This code copies from and is heavily based on the nice PyPi module 'microscoper'.
https://github.com/pskeshu/microscoper
"""

# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))

import os
import bioformats as bf
import javabridge as jb
import xml.dom.minidom
import numpy as np
import argparse
import datetime
from pathlib import Path
import json
from utils.vesseg_logger import VessegLogger
from PIL import Image


def walk_directory_to_list(input_directory, val_fxn=lambda x: x.endswith('.vsi') and 'temp' not in x):
    """Walks input directory to file list for bioformats reader. Takes a filepath validation function.
    """
    filelist = []
    for root, dirs, files in os.walk(input_directory):
        for file in files:
            filepath = os.path.join(root, file)
            if val_fxn(filepath):
                filelist.append(filepath)
    return filelist


def get_metadata(filename):
    """Read the meta data and return the metadata object.
    """
    meta = bf.get_omexml_metadata(filename)
    metadata = bf.omexml.OMEXML(meta)
    return metadata


def save_metadata(metadata, filename, output_directory):
    """Save metadata."""
    data = xml.dom.minidom.parseString(metadata.to_xml())
    pretty_xml_as_string = data.toprettyxml()

    with open(os.path.join(output_directory, filename), "w") as xmlfile:
        xmlfile.write(pretty_xml_as_string)


def read_images(path, return_largest_only=True):
    """Read image from path. Return it as a numpy array."""
    with bf.ImageReader(path) as reader:
        c_total = reader.rdr.getSizeC()
        z_total = reader.rdr.getSizeZ()
        t_total = reader.rdr.getSizeT()

        # No support for hyperstacks.
        if 1 not in [z_total, t_total]:
            raise TypeError("Only 4D images are currently supported.")

        max_image_size = 0
        all_images = []

        for channel in range(c_total):
            images = []
            for time in range(t_total):
                for z in range(z_total):
                    image = reader.read(c=channel, z=z, t=time, rescale=False)
                    images.append(image)
            image_array = np.asarray(images).squeeze()
            if return_largest_only:
                if np.product(image_array.shape[:2]) > max_image_size:
                    max_image_size = np.product(image_array[:2])
                    all_images = [image_array]
            else:
                all_images.append(image_array)

    return all_images


def save_images(image_array, filename, output_directory):
    """ Save image array using PIL."""
    img = Image.fromarray(image_array)
    img.save(os.path.join(output_directory, filename))


def make_logger():
    """
    Avoid bioformats error messages.
    Copied from https://github.com/CellProfiler/python-bioformats/
    """
    jb.static_call("org/apache/log4j/BasicConfigurator", "configure", "()V")
    log4j_logger = jb.static_call("org/apache/log4j/Logger","getRootLogger", "()Lorg/apache/log4j/Logger;")
    warn_level = jb.get_static_field("org/apache/log4j/Level", "WARN", "Lorg/apache/log4j/Level;")
    jb.call(log4j_logger, "setLevel", "(Lorg/apache/log4j/Level;)V", warn_level)


def prettify_filename(filename): return filename.replace(' ', '_').replace('.', '_')


def log_printer(log_type, message):
    log_dict = {
        'module': Path(__file__).stem, 
        'timestamp': str(datetime.datetime.now()), 
        'log_type': log_type, 
        'message': message
    }
    print(json.dumps(log_dict), flush=True)


def converter(input_directory, output_directory, conversion_file_type: str, save_file_type: str) -> None:
    """
    Converts proprietary microscopy format using bioformats.
        Params:
            input_directory (Path, str): Input directory path
            output_directory (Path, str): Output directory path
            conversion_file_type (str): Proprietary file type to look for and try to convert
            save_file_type (str): Pillow savable file type.
        Returns: None
    """

    vl = VessegLogger()
    
    img_dir = os.path.join(output_directory)
    meta_dir = os.path.join(output_directory, 'metadata')
    Path(img_dir).mkdir(parents=True, exist_ok=True)
    Path(meta_dir).mkdir(parents=True, exist_ok=True)

    jb.start_vm(class_path=bf.JARS, max_heap_size="8G")
    make_logger()
    files = walk_directory_to_list(input_directory, lambda x: x.endswith(conversion_file_type) and 'temp' not in x)

    vl.p(log_type='info', message=f'Starting conversion, {len(files)} files found.')
    vl.p(log_type='status', message='0')

    for i, file in enumerate(files, start=1):

        pretty_filename_stem = prettify_filename(file.split('/')[-1].replace('.' + conversion_file_type, ''))
        file_pil = pretty_filename_stem + '.' + save_file_type
        file_xml = pretty_filename_stem + '.xml'

        # Get and save metadata
        metadata = get_metadata(file)
        save_metadata(metadata, file_xml, meta_dir)

        # Read and save images.
        all_images = read_images(file)
        if len(all_images) == 1:
            save_images(all_images[0], file_pil, img_dir)
        else:
            for j, image in enumerate(all_images):
                file_pil = file_pil.replace('.{}'.format(save_file_type), '_{}.{}'.format(str(j), save_file_type))
                save_images(image, file_pil, img_dir)

        vl.p(log_type='status', message=f'{round(i/len(files),4)}')

    jb.kill_vm()

    vl.p(log_type='info', message=f'Stopping conversion')  

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='file type converter')
    parser.add_argument('-i', '--input_directory', type=str, required=True, help='input directory for conversion')
    parser.add_argument('-o', '--output_directory', type=str, required=True, help='output directory for conversion')
    parser.add_argument('-l', '--log_directory', type=str, required=False, help='directory for logs')
    parser.add_argument('-d', '--log_dictionary', type=dict, default={}, required=False, help='base dictionary for printing/logging.')
    parser.add_argument('-sft', '--save_file_type', default='png', required=False, help='PIL savable file type ending')
    parser.add_argument('-cft', '--conversion_file_type', default='vsi', required=False, help='Proprietary format to convert.')
    args = parser.parse_args()


    converter(args.input_directory, args.output_directory, args.conversion_file_type, args.save_file_type)
