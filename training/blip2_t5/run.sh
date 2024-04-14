#!/bin/bash


python train.py \
    --output_dir ./blip2_t5_finetuned \
    --model_name_or_path ../../weights/blip2_t5/projection \
    --data_dir $(dirname `pwd`)/datasets/coco \
    --data_cache_dir $(dirname `pwd`)/datasets/coco/data \
    --dataset_name ydshieh/coco_dataset_script \
    --dataset_config_name=2017 \
    --image_column image_path \
    --caption_column caption \
    --remove_unused_columns=False \
    --do_train \
    --do_eval \
    --per_device_train_batch_size 64 \
    --per_device_eval_batch_size 64 \
    --learning_rate="5e-5" \
    --warmup_steps 0 \
    --weight_decay 0.1 \
    --freeze_vision_model \
    --freeze_text_model