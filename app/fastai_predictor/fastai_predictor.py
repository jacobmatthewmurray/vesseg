# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))

from fastai.vision import *
from PIL import Image as PILImage
from pathlib import Path
import warnings
import argparse
warnings.filterwarnings("ignore")
from utils.vesseg_logger import VessegLogger


def walk_directory_to_list(input_directory, val_fxn=lambda x: x.endswith('.png')):
    """ Walks input directory to file list. Takes a filepath validation function. """
    file_list = []
    for root, dirs, files in os.walk(input_directory):
        for file in files:
            filepath = os.path.join(root, file)
            if val_fxn(filepath):
                file_list.append(filepath)
    return file_list


def predict_fastai(input_directory, output_directory, model_directory, chunk_size=50):
    """ Predict PIL readable images with fastai model. Model is average of models in model directory. """

    # Retrieve learners for prediction
    learners = walk_directory_to_list(model_directory, lambda x: x.endswith('.pkl'))

    # Retrieve dataset for prediction
    data = SegmentationItemList.from_folder(input_directory)

    # Generate logger
    vl = VessegLogger()
    vl.p(log_type='info', message=f'Starting fastai prediction, {len(data)} files found.')
    vl.p(log_type='status', message='0')

    for k in range(0, len(data), chunk_size):

        data_chunk = data[k:k+chunk_size]
        all_preds = []


        for l in learners:
            learner_path = Path(l)
            learn = load_learner(learner_path.parent, file=learner_path.name)
            preds = [learn.predict(d)[2].numpy() for d in data_chunk]
            all_preds.append(np.stack(preds))

        all_preds = np.stack(all_preds)
        mean_preds = np.mean(all_preds, axis=0)
        all_labels = np.argmax(mean_preds, axis=1)

        for i in range(len(data_chunk)):
            vl.p(log_type='status', message=f'{round((k+i+1)/len(data),4)}')

            name, labels = data_chunk.items[i].name, all_labels[i, ...].astype('uint8')
            msk = PILImage.fromarray(labels)
            Path(output_directory).mkdir(parents=True, exist_ok=True)
            msk.save(os.path.join(output_directory, name), optimize=True)

    vl.p(log_type='info', message=f'Stopping fastai prediction.')  


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_folder', required=True)
    parser.add_argument('-o', '--output_folder', required=True)
    parser.add_argument('-m', '--model_folder', required=True)
    parser.add_argument('-c', '--chunk_size', required=False, default=50)
    args = parser.parse_args()

    predict_fastai(args.input_folder, args.output_folder, args.model_folder, args.chunk_size)