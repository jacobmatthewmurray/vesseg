#!/usr/bin/env bash

echo "***********************************************************************"
echo "***** Combining meta data info"
echo "***********************************************************************"

echo "***********************************************************************"
echo "***** Building necessary containers"
echo "***********************************************************************"

docker build -t processor:latest -f processor/Dockerfile https://github.com/jacobmatthewmurray/vesseg.git#:app


echo "Enter path to analysis folder:"
read CMI_ANALYSIS_FOLDER
echo "Enter path to output folder:"
read CMI_OUTPUT_FOLDER
echo "Enter path to .vsi folder:"
read CMI_VIS_FOLDER






for container in "$@"
do
    echo "***********************************************************************"
    echo "***** Building container $container !"
    echo "***********************************************************************"
    docker build -t "$container":latest -f "$container"/Dockerfile .
done 