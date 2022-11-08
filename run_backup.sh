#!/bin/bash
current_dir="$(pwd)"
docker run --rm -v $current_dir/code:/code -v /fs:/fs --net=host --env-file=$current_dir/env.list stats:v1 python3 /code/cvat_com.py --backup=True --filepath=/fs/sefs1/backup --filepath=/fs/sefs2/backup
