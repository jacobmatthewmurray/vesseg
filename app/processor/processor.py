#!/usr/bin/env python3

# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))

# Import 
import numpy as np
import pandas as pd
import os
import argparse
import json
from matplotlib.cm import ScalarMappable as mpl_scalar_mappable
from matplotlib.colors import Normalize as mpl_norm
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from pathlib import Path
import xml.etree.ElementTree as ET
from utils.vesseg_logger import VessegLogger


def walk_directory_to_files(input_directory, file_select_fxn=lambda x: x.endswith('.png')):
    file_list = []

    if not os.path.isdir(input_directory):
        return file_list

    for root, dirs, files in os.walk(input_directory):
        for file in files:
            if file_select_fxn(os.path.join(root, file)):
                file_list.append(os.path.join(root, file))
    return file_list


def create_overlay(img, dest, vl, num_labels=3, color_map='viridis', alpha=0.3):

    Path(dest).mkdir(parents=True, exist_ok=True)
    file_name = Path(img).name
    msk = Path(dest).parent / 'masks' / file_name

    img_arr = np.array(Image.open(img))
    msk_arr = np.array(Image.open(msk))

    sm = mpl_scalar_mappable(mpl_norm(0, num_labels-1), color_map)
    cm_arr_rgba = sm.to_rgba(msk_arr)
    cm_arr_rgba = (cm_arr_rgba*255).astype('uint8')
    cm_arr_rbga_img = Image.fromarray(cm_arr_rgba, mode='RGBA')

    alpha_channel = np.full((*img_arr.shape[:2], 1), 255, dtype='uint8')
    img_arr_rgba = np.concatenate((img_arr, alpha_channel), axis=-1).astype('uint8')
    img_arr_rgba_img = Image.fromarray(img_arr_rgba, mode='RGBA')

    ol_img = Image.blend(img_arr_rgba_img, cm_arr_rbga_img, alpha)
    Path(dest).mkdir(parents=True, exist_ok=True)
    ol_img.save(Path(dest)/ Path(img).name, optimize=True)


def resize(img, dest, vl, new_size=(512,512), new_file_type='.png'):
    
    file_name = Path(img).stem
    Path(dest).mkdir(parents=True, exist_ok=True)

    img = Image.open(img)
    resized_img = img.resize(new_size, resample=Image.BICUBIC)

    if 'png' in new_file_type.lower():
        png_info_dict = {
            'original_width': img.width,
            'original_height': img.height,
            'resized_width': resized_img.width,
            'resized_height': resized_img.height
        }
        png_info = PngInfo()
        for key, value in png_info_dict.items():
            png_info.add_text(key, str(value))
        resized_img.save(os.path.join(dest, file_name + '.' + new_file_type.replace('.', '')), 'PNG', optimize=True, pnginfo=png_info)
    else:
        resized_img.save(os.path.join(dest, file_name + '.' + new_file_type.replace('.', '')))

        
def convert_mode(img, dest, vil, new_mode='RGB', new_file_type='.png'):
    file_name = Path(img).stem
    Path(dest).mkdir(parents=True, exist_ok=True)
    img = Image.open(img)
    converted_img = img.convert(new_mode)
    converted_img.save(os.path.join(dest, file_name + '.' + new_file_type.replace('.', '')))


def pil_to_png(img, dest, vil):
    file_name = Path(img).stem
    Path(dest).mkdir(parents=True, exist_ok=True)
    img = Image.open(img)
    img.save(os.path.join(dest, file_name + '.png'))



def processor(processor_fxn, input_folder, output_folder, kwargs):

    file_list = walk_directory_to_files(input_folder)

    # Generate logger
    vl = VessegLogger()
    vl.p(log_type='info', message=f'Starting processing with {processor_fxn.__name__}, {len(file_list)} files found.')
    vl.p(log_type='status', message='0')

    for i, f in enumerate(file_list, start=1):
        vl.p(log_type='status', message=f'{round(i/len(file_list),4)}')
        processor_fxn(f, output_folder, vl, **kwargs)

    vl.p(log_type='info', message=f'Stopping processing with {processor_fxn.__name__}.')  


def get_um_length_from_metadata(metadata_xml):

    requested_attributes = [
        'PhysicalSizeX',
        'PhysicalSizeY',
        'PhysicalSizeXUnit',
        'PhysicalSizeYUnit',
        'SizeX',
        'SizeY'
    ]

    ns = {'ome': 'http://www.openmicroscopy.org/Schemas/OME/2016-06'}

    tree = ET.parse(metadata_xml)
    elem = tree.find(".//ome:Image[@ID='Image:0']/ome:Pixels", ns)

    return_dict = dict()

    for a in requested_attributes:
        return_dict[a] = elem.get(a)

    return return_dict



def analyzer(input_folder, kwargs):

    vl = VessegLogger()
    predictionmodel_name = kwargs.get('predictionmodel_name')

    if not predictionmodel_name:
        vl.p(log_type='error', message='Analyzer called without predictionmodel_name')
        return None

    # Determine number of files to analyze

    preprocessed_path = Path(input_folder, 'preprocessed')
    mask_path = Path(input_folder, 'predicted', predictionmodel_name, 'masks')
    analysis_path = Path(input_folder, 'analysis')
    analysis_path.mkdir(exist_ok=True, parents=True)

    meta_data = walk_directory_to_files(preprocessed_path, lambda x: x.endswith('.xml'))
    images = walk_directory_to_files(preprocessed_path, lambda x: x.endswith('.png'))   
    masks = walk_directory_to_files(mask_path, lambda x: x.endswith('.png'))   
    total_files = len(meta_data) + len(images) + len(masks)

    vl.p(log_type='info', message=f'Starting processing, {total_files} files found.')
    
    if total_files==0:
        return None

    meta_info = []
    for c, i in enumerate(meta_data, start=1): 
        vl.p(log_type='status', message=f'{round(c/total_files,4)}')
        image = Path(i).stem
        xml_dict= get_um_length_from_metadata(i)
        meta_info.append({
            'image': image,
            'x_length': xml_dict['PhysicalSizeX'], 
            'y_length': xml_dict['PhysicalSizeY'], 
            'x_length_unit': xml_dict['PhysicalSizeXUnit'],
            'y_legnth_unit': xml_dict['PhysicalSizeYUnit'] 
        })

    image_info = []
    for c, i in enumerate(images, start=len(meta_data)+1):
        vl.p(log_type='status', message=f'{round(c/total_files,4)}')
        image = Path(i).stem
        img = Image.open(i)
        image_info.append({
            'image': image, 
            'original_width': img.info['original_width'] ,
            'original_height': img.info['original_height'], 
            'resized_width': img.info['resized_width'],
            'resized_height': img.info['resized_height']
        })

    mask_info = []
    for c, i in enumerate(masks, start=len(meta_data)+len(images)+1):
        vl.p(log_type='status', message=f'{round(c/total_files,4)}')
        mask = Path(i).stem
        msk_arr = np.array(Image.open(i))
        background_pixels = int(np.sum(msk_arr == 0))
        lumen_pixels = int(np.sum(msk_arr == 2))
        plaque_pixels = int(np.sum(msk_arr == 1))
        mask_info.append({
            'image': mask,
            predictionmodel_name + '_background_pixels': background_pixels, 
            predictionmodel_name + '_lumen_pixels': lumen_pixels, 
            predictionmodel_name + '_plaque_pixels': plaque_pixels,
            predictionmodel_name + '_occlusion_fraction': plaque_pixels/(lumen_pixels+plaque_pixels)
        })
        
    df_meta = pd.DataFrame(meta_info)
    df_image = pd.DataFrame(image_info)
    df_mask = pd.DataFrame(mask_info)

    df = df_image.merge(df_meta, how='left', on='image')
    df = df.merge(df_mask, how='left', on='image')

    df.to_csv(Path(analysis_path, predictionmodel_name + '_analysis.csv'), index=False)
        
    vl.p(log_type='info', message=f'Processing complete.')


if __name__=="__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--function', required=True)
    parser.add_argument('-i', '--input_folder', required=True)
    parser.add_argument('-o', '--output_folder', required=True)
    parser.add_argument('-k', '--kwargs', required=False, type=str, default='{}')
    args = parser.parse_args()

    if args.function == 'analyzer':
        analyzer(args.input_folder, json.loads(args.kwargs))
    else:
        processor(globals()[args.function], args.input_folder, args.output_folder, json.loads(args.kwargs))

    


    