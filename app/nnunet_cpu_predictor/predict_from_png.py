import argparse
import subprocess
from nnunet.inference.predict import predict_from_folder
import tempfile
from nnunet.paths import default_plans_identifier, network_training_output_dir
import os
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from pathlib import Path
import numpy as np
import nibabel as nib


def png_to_niigz(file_path, out_dir):
    affine = np.eye(4)
    img_array = np.array(Image.open(file_path))

    for i in range(3):
        nifti_img = nib.Nifti1Image(np.expand_dims(img_array[:, :, i], axis=-1), affine)
        new_filename = os.path.basename(file_path).replace('.png',  '_' + ('000' + str(i))[-4:] + '.nii.gz')
        nib.save(nifti_img, os.path.join(out_dir, new_filename))

def niigz_to_png(file_path, out_dir):
    img_array = nib.load(file_path).get_fdata().astype('uint8').squeeze()
    img = Image.fromarray(img_array)
    filename = os.path.basename(file_path).replace('.nii.gz', '.png')
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    img.save(os.path.join(out_dir, filename))


def predict_from_png(input_directory, output_directory, task, nnunet_version):

    with tempfile.TemporaryDirectory() as tmpdir:
        
        os.mkdir(os.path.join(tmpdir, 'in'))
        os.mkdir(os.path.join(tmpdir, 'out'))
        
        for file in os.listdir(input_directory):
            if file.endswith('.png'):
                png_to_niigz(os.path.join(input_directory, file), os.path.join(tmpdir, 'in'))

        if nnunet_version < 2: 

            output_folder = os.path.join(tmpdir, 'out')
            input_folder = os.path.join(tmpdir, 'in')
            output_folder_name = os.path.join(network_training_output_dir, '2d', task, "nnUNetTrainer__" + default_plans_identifier)
            folds = None 
            save_npz = None 
            num_threads_preprocessing = 6
            num_threads_nifti_save = 2
            lowres_segmentations = None
            part_id = 0
            num_parts = 1
            tta = 1
            overwrite = 1

            predict_from_folder(output_folder_name, input_folder, output_folder, folds, save_npz, num_threads_preprocessing, num_threads_nifti_save, lowres_segmentations, part_id, num_parts, tta, overwrite_existing=overwrite)

        else:
            subprocess.run(['nnUNet_predict', '-i', os.path.join(tmpdir, 'in'), '-o', os.path.join(tmpdir, 'out'), '-t', task, '-m', '2d'])

        for file in os.listdir(os.path.join(tmpdir, 'out')):
            if file.endswith('.nii.gz'):
                niigz_to_png(os.path.join(tmpdir, 'out', file), output_directory)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_folder', required=True)
    parser.add_argument('-o', '--output_folder', required=True)
    parser.add_argument('-t', '--task', required=True)
    parser.add_argument('-m', '--model_folder', required=True)
    parser.add_argument('-n', '--nnunet_version', required=False, default=2)
    args = parser.parse_args()

    os.environ['RESULTS_FOLDER'] = args.model_folder

    predict_from_png(args.input_folder, args.output_folder, args.task, nnunet_version=int(args.nnunet_version))

