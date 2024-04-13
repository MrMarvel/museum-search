#!/bin/bash

python3 download_model.py


python3 convert_text_checkpoint.py \
    -i /weights/blip2_t5/text_model \
    -o /weights/blip2_t5/text_model/converted_ckpt \
    --weight_data_type float32 \
    --inference_tensor_para_size 1


python3 build_text_engine.py \
    --model_type t5 \
    --weight_dir /weights/blip2_t5/text_model/converted_ckpt/tp1 \
    --output_dir /weights/blip2_t5/text_model_tensorrt \
    --engine_name model \
    --remove_input_padding \
    --use_bert_attention_plugin \
    --use_gpt_attention_plugin \
    --use_gemm_plugin \
    --dtype bfloat16 \
    --max_beam_width 1 \
    --max_batch_size 8 \
    --max_encoder_input_len 924 \
    --max_output_len 100 \
    --max_multimodal_len 256


python3 build_vision_engine.py \
     --output_dir /weights/blip2_t5/vision_model_tensorrt \
     --model_path /weights/blip2_t5/model \
     --max_batch_size 8


trtexec \
    --onnx=/weights/blip2_t5/vision_model_tensorrt/onnx/visual_encoder.onnx \
    --minShapes=input:1x3x364x364 \
    --optShapes=input:4x3x364x364 \
    --maxShapes=input:8x3x364x364 \
    --saveEngine=/weights/blip2_t5/vision_model_tensorrt/visual_encoder_fp16.plan \
    --fp16 \
    --verbose




# АХТУНГ. ЗАПУСКАТЬ ТОЛЬКО ЕСЛИ ЗНАЕШЬ, ЧТО ДЕЛАЕШЬ
# МОГУТ НЕ СОВПАДАТЬ ВЕРСИИ TensorRT
# python3 run.py \
#     --blip2_encoder \
#     --max_new_tokens 30 \
#     --input_text "" \
#     --hf_model_dir /weights/blip2_t5/model \
#     --visual_engine_dir /weights/blip2_t5/vision_model_tensorrt \
#     --llm_engine_dir /weights/blip2_t5/text_model_tensorrt