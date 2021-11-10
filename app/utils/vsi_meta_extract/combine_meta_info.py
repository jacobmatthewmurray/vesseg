#!/usr/bin/env python3

import argparse
import os
import pandas as pd
import xml.etree.ElementTree as ET
from functools import reduce



def walk_directory_to_files(input_directory, file_select_fxn=lambda x: x.endswith('.png')):
    file_list = []

    if not os.path.isdir(input_directory):
        return file_list

    for root, dirs, files in os.walk(input_directory):
        for file in files:
            if file_select_fxn(os.path.join(root, file)):
                file_list.append(os.path.join(root, file))
    return file_list


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


def combine(analysis_dir: str, output_dir: str): 

    als = walk_directory_to_files(analysis_dir, lambda x: x.endswith('.csv'))
    dfs = [pd.read_csv(a) for a in als]

    assert len(dfs)>0, f'No analysis files in {analysis_dir}. Analysis files are needed.'

    models = [a.split('/')[-1].replace('_analysis.csv', '') for a in als if not a.startswith('evaluation')]
    if len(dfs)>1:
        df = reduce(lambda l,r: pd.merge(l,r,on='image', how='inner'), dfs)
    else:
        df = dfs[0]

    mds = walk_directory_to_files(output_dir, lambda x: x.endswith('.xml'))
    mds = [m for m in mds if '/metadata/' in m]

    meta_info = []
    for m in mds: 
        xml_dict = get_um_length_from_metadata(m)
        image = m.split('/')[-1].split('.')[0]
        meta_info.append({
            'image': image,
            'x_length': xml_dict['PhysicalSizeX'], 
            'y_length': xml_dict['PhysicalSizeY'], 
            'x_length_unit': xml_dict['PhysicalSizeXUnit'],
            'y_legnth_unit': xml_dict['PhysicalSizeYUnit'] 
        })
    meta_info_df = pd.DataFrame(meta_info)
    df = df.merge(meta_info_df, how='left', on='image')

    for i in ['resized', 'original']:
        for j in ['height', 'width']:
            df['_'.join([i,j])] = df['_'.join([i,j])].astype(int)
    for i in ['x', 'y']:
        df[f'{i}_length'] = df[f'{i}_length'].astype(float)

    for m in models: 
        for l in ['plaque', 'lumen', 'background']:
            df[f'{m}_{l}_pixels'] = df[f'{m}_{l}_pixels'].astype(int)
            df['_'.join([m, 'physical', l, 'size'])] = (df['original_width']/df['resized_width'])*(df['original_height']/df['resized_height'])*(df['x_length']*df['y_length'])*df[f'{m}_{l}_pixels']
    
    df.to_csv(os.path.join(analysis_dir, 'final_analysis.csv'), index=False)

    return None


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='meta combinator')
    parser.add_argument('-a', '--analysis_directory', type=str, required=True, help='analysis directory')
    parser.add_argument('-o', '--output_directory', type=str, required=True, help='output directory')
    args = parser.parse_args()
    combine(args.analysis_directory, args.output_directory)