#!/usr/bin/env bash

echo "***********************************************************************"
echo "***** Combining meta data info"
echo "***********************************************************************"

docker build -t cmi:latest .
docker build -t file_type_converter:latest  ../../file_type_converter


echo "Enter path to analysis folder:"
read CMI_ANALYSIS_FOLDER
echo "Enter path to output folder:"
read CMI_OUTPUT_FOLDER
echo "Enter path to .vsi folder:"
read CMI_VIS_FOLDER


docker run -v $CMI_VIS_FOLDER:$CMI_VIS_FOLDER -v $CMI_OUTPUT_FOLDER:$CMI_OUTPUT_FOLDER file_type_converter:latest -i $CMI_VIS_FOLDER -o $CMI_OUTPUT_FOLDER
docker run -v $CMI_ANALYSIS_FOLDER:$CMI_ANALYSIS_FOLDER -v $CMI_OUTPUT_FOLDER:$CMI_OUTPUT_FOLDER cmi:latest -a $CMI_ANALYSIS_FOLDER -o $CMI_OUTPUT_FOLDER

echo "***********************************************************************"
echo "***** COMPLETE! Check your final analysis in the folder $CMI_ANALYSIS_FOLDER"
echo "***********************************************************************"