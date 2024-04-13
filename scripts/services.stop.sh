#!/bin/bash

sudo docker compose -f docker/milvus.yaml down
sudo docker compose -f docker/rabbit.yaml down
sudo docker compose -f docker/triton.yaml down