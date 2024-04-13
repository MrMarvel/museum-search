#!/bin/bash

python3 convert.py

trtexec \
	--onnx=/weights/blip2_t5/classification/mlp.onnx \
	--minShapes=input:1x1408 \
	--optShapes=input:4x1408 \
	--maxShapes=input:8x1408 \
	--saveEngine=/weights/blip2_t5/classification/mlp.plan \
	--device=0 \
	--fp16 \
	--verbose