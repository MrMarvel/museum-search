#!/bin/bash

sudo docker compose -f docker/milvus.yaml up -d
sudo docker compose -f docker/rabbit.yaml up -d
sudo docker compose -f docker/triton.yaml up -d