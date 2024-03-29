#!/usr/bin/env bash

echo "Make sure to run this script from app directory ./utils/build_all_container.sh"
echo "Script takes arguments of the names of the containers to be build, i.e., processor."

for container in "$@"
do
    echo "***********************************************************************"
    echo "***** Building container $container !"
    echo "***********************************************************************"
    docker build -t "$container":latest -f "$container"/Dockerfile .
done 