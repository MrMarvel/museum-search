import argparse
import os
import sys
from pathlib import Path

import numpy as np
import requests

# isort: off
import torch
import tensorrt as trt
# isort: on

from huggingface_hub import hf_hub_download
from PIL import Image
from transformers import (AutoConfig, AutoProcessor, AutoTokenizer,
                          Blip2Processor, NougatProcessor, NougatTokenizerFast)

import tensorrt_llm
import tensorrt_llm.profiler as profiler
from tensorrt_llm import logger
from tensorrt_llm._utils import torch_to_numpy
from tensorrt_llm.runtime import ModelRunner, Session, TensorInfo

from model import TRTLLMEncDecModel


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max_new_tokens', type=int, default=30)
    parser.add_argument('--batch_size', type=int, default=1)
    parser.add_argument('--log_level', type=str, default='info')
    parser.add_argument('--visual_engine_dir',
                        type=str,
                        default=None,
                        help='Directory containing visual TRT engines')
    parser.add_argument('--llm_engine_dir',
                        type=str,
                        default=None,
                        help='Directory containing TRT-LLM engines')
    parser.add_argument('--hf_model_dir',
                        type=str,
                        default=None,
                        help="Directory containing tokenizer")
    parser.add_argument(
        '--decoder_llm',
        action='store_true',
        help='Whether LLM is decoder-only or an encoder-decoder variant?')
    parser.add_argument('--blip2_encoder',
                        action='store_true',
                        help='Whether visual encoder is a BLIP2 model')
    parser.add_argument('--nougat',
                        action='store_true',
                        help='Run nougat pipeline')
    parser.add_argument('--input_text',
                        type=str,
                        default='Question: which city is this? Answer:',
                        help='Text prompt to LLM')
    parser.add_argument('--num_beams',
                        type=int,
                        help="Use beam search if num_beams >1",
                        default=1)
    parser.add_argument('--top_k', type=int, default=1)

    return parser.parse_args()


def trt_dtype_to_torch(dtype):
    if dtype == trt.float16:
        return torch.float16
    elif dtype == trt.float32:
        return torch.float32
    elif dtype == trt.int32:
        return torch.int32
    else:
        raise TypeError("%s is not supported" % dtype)


class MultiModalModel:

    def __init__(self, args):
        self.args = args

        runtime_rank = tensorrt_llm.mpi_rank()
        device_id = runtime_rank % torch.cuda.device_count()
        torch.cuda.set_device(device_id)
        self.stream = torch.cuda.current_stream().cuda_stream

        self.init_image_encoder()
        self.init_tokenizer()
        self.init_llm()

    def init_tokenizer(self):
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.args.hf_model_dir, use_fast=False, use_legacy=False)

        self.tokenizer.padding_side = "right"
        # self.tokenizer.pad_token = self.tokenizer.eos_token

    def init_image_encoder(self):
        vit_path = os.path.join(self.args.visual_engine_dir,
                                'visual_encoder_fp16.plan')
        logger.info(f'Loading engine from {vit_path}')
        with open(vit_path, 'rb') as f:
            engine_buffer = f.read()
        logger.info(f'Creating session from engine {vit_path}')
        self.visual_encoder_session = Session.from_serialized_engine(
            engine_buffer)

    def init_llm(self):
        self.model = TRTLLMEncDecModel.from_engine(
            os.path.basename(self.args.hf_model_dir),
            self.args.llm_engine_dir,
            skip_encoder=self.args.nougat,
            debug_mode=False)

        self.model_config = self.model.encoder_model_config
        self.runtime_mapping = self.model.encoder_runtime_mapping

        config = AutoConfig.from_pretrained(self.args.hf_model_dir).text_config
        decoder_start_id = config.decoder_start_token_id
        if decoder_start_id is None:
            decoder_start_id = self.tokenizer.bos_token_id

        decoder_input_ids = torch.IntTensor([[decoder_start_id]]).to("cuda")
        batch_size = self.args.batch_size
        self.decoder_input_ids = decoder_input_ids.repeat((batch_size, 1))

    def generate(self, pre_prompt, post_prompt, image, max_new_tokens):
        profiler.start("Generate")
        profiler.start("Vision")
        visual_features, visual_atts, _ = self.get_visual_features(image)
        # print(visual_features)
        # print(_)
        profiler.stop("Vision")

        pre_input_ids = self.tokenizer(pre_prompt,
                                       return_tensors="pt",
                                       padding=True).input_ids.to("cuda")
        # print(pre_input_ids)
        if post_prompt[0] is not None:
            post_input_ids = self.tokenizer(post_prompt,
                                            return_tensors="pt",
                                            padding=True).input_ids.to("cuda")
            length = pre_input_ids.shape[1] + post_input_ids.shape[
                1] + visual_atts.shape[1]
        else:
            post_input_ids = None
            length = pre_input_ids.shape[1] + visual_atts.shape[1]

        input_lengths = torch.IntTensor([length] * args.batch_size).to(
            torch.int32).to("cuda")
        input_ids, ptuning_args = self.setup_fake_prompts(
            visual_features, pre_input_ids, post_input_ids, input_lengths)

        profiler.start("LLM")
        # print(input_ids)
        # print(self.decoder_input_ids)
        # print(ptuning_args[0])
        # print(ptuning_args[1])
        # print(ptuning_args[2])
        output_ids = self.model.generate(
            input_ids,
            self.decoder_input_ids,
            max_new_tokens,
            num_beams=self.args.num_beams,
            bos_token_id=self.tokenizer.bos_token_id,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            debug_mode=False,
            prompt_embedding_table=ptuning_args[0],
            prompt_tasks=ptuning_args[1],
            prompt_vocab_size=ptuning_args[2])

        # Reset input_lengths to match decoder_input_ids
        input_lengths = torch.ones(input_lengths.shape,
                                    dtype=input_lengths.dtype)
        profiler.stop("LLM")

        if tensorrt_llm.mpi_rank() == 0:
            # Extract a list of tensors of shape beam_width x output_ids.
            output_beams_list = [
                self.tokenizer.batch_decode(
                    output_ids[batch_idx, :, input_lengths[batch_idx]:],
                    skip_special_tokens=True)
                for batch_idx in range(self.args.batch_size)
            ]

            stripped_text = [[
                output_beams_list[batch_idx][beam_idx].strip()
                for beam_idx in range(self.args.num_beams)
            ] for batch_idx in range(self.args.batch_size)]
            profiler.stop("Generate")
            return stripped_text
        else:
            profiler.stop("Generate")
            return None

    def get_visual_features(self, image):
        visual_features = {'input': image.half()}
        visual_output_info = self.visual_encoder_session.infer_shapes(
            [TensorInfo('input', trt.DataType.HALF, image.shape)])
        visual_outputs = {
            t.name: torch.empty(tuple(t.shape),
                                dtype=trt_dtype_to_torch(t.dtype),
                                device="cuda")
            for t in visual_output_info
        }

        ok = self.visual_encoder_session.run(visual_features, visual_outputs,
                                             self.stream)
        assert ok, "Runtime execution failed for vit session"
        torch.cuda.synchronize()

        image_embeds = visual_outputs['output']
        image_features = visual_outputs['pooled_output']
        image_atts = torch.ones(image_embeds.size()[:-1],
                                dtype=torch.long).to("cuda")

        print(image_embeds.shape, image_features.shape)
        return image_embeds, image_atts, image_features

    def setup_fake_prompts(self, visual_features, pre_input_ids, post_input_ids,
                           input_lengths):
        # Assemble fake prompts which points to image embedding actually
        fake_prompt_id = torch.arange(
            self.model_config.vocab_size,
            self.model_config.vocab_size +
            visual_features.shape[0] * visual_features.shape[1],
            device="cuda")
        fake_prompt_id = fake_prompt_id.reshape(visual_features.shape[0],
                                                visual_features.shape[1])

        if post_input_ids is not None:
            input_ids = [pre_input_ids, fake_prompt_id, post_input_ids]
        else:
            input_ids = [fake_prompt_id, pre_input_ids]
        input_ids = torch.cat(input_ids,
                              dim=1).contiguous().to(torch.int32).cuda()

        if self.args.decoder_llm or self.runtime_mapping.is_first_pp_rank():
            ptuning_args = self.ptuning_setup(visual_features, input_ids,
                                              input_lengths)
        else:
            ptuning_args = [None, None, None]

        return input_ids, ptuning_args

    def ptuning_setup(self, prompt_table, input_ids, input_lengths):
        if prompt_table is not None:
            task_vocab_size = torch.tensor([prompt_table.shape[1]],
                                           dtype=torch.int32,
                                           device="cuda")
            prompt_table = prompt_table.view(
                (prompt_table.shape[0] * prompt_table.shape[1],
                 prompt_table.shape[2]))

            hidden_size = self.model_config.hidden_size
            if not self.args.decoder_llm:
                hidden_size *= self.runtime_mapping.tp_size
            assert prompt_table.shape[
                1] == hidden_size, "Prompt table dimensions do not match hidden size"

            prompt_table = prompt_table.cuda().to(
                dtype=tensorrt_llm._utils.str_dtype_to_torch(
                    self.model_config.dtype))
        else:
            prompt_table = torch.empty([1, hidden_size]).cuda()
            task_vocab_size = torch.zeros([1]).cuda()

        if self.model_config.remove_input_padding:
            tasks = torch.zeros([torch.sum(input_lengths)],
                                dtype=torch.int32).cuda()
            if args.decoder_llm: tasks = tasks.unsqueeze(0)
        else:
            tasks = torch.zeros(input_ids.shape, dtype=torch.int32).cuda()

        return [prompt_table, tasks, task_vocab_size]


def load_test_image(model_name):
    img_url = 'https://sun1-92.userapi.com/impg/fnn1LcU9RbFGAk8Y64_WCB0nrAzjJKFa-5EpZg/STS6yLrU-XI.jpg?size=640x480&quality=95&sign=dab78f730e79022d36a499e0ae1783be&type=album'
    image = Image.open(requests.get(img_url,
                                    stream=True).raw).convert('RGB')

    return image


if __name__ == '__main__':
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    args = parse_arguments()
    tensorrt_llm.logger.set_level(args.log_level)
    runtime_rank = tensorrt_llm.mpi_rank()

    image = load_test_image(args.hf_model_dir)

    processor = Blip2Processor.from_pretrained('/weights/blip2_t5/model')

    inputs = processor(image, args.input_text,
                        return_tensors="pt").to("cuda")
    image = inputs['pixel_values']
    image = image.expand(args.batch_size, -1, -1,
                            -1).contiguous().to("cuda")

    pre_prompt = args.input_text
    post_prompt = None

    # Repeat inputs to match batch size
    pre_prompt = [pre_prompt] * args.batch_size
    post_prompt = [post_prompt] * args.batch_size
    image = image.expand(args.batch_size, -1, -1, -1).contiguous()

    model = MultiModalModel(args)

    num_iters = 100
    for _ in range(num_iters):
        stripped_text = model.generate(pre_prompt, post_prompt, image,
                                       args.max_new_tokens)

    if runtime_rank == 0:
        logger.info("---------------------------------------------------------")
        logger.info(f"\n[Q] {args.input_text}")
        logger.info(f"\n[A] {stripped_text}")
        logger.info(
            f'TensorRT vision encoder latency: {profiler.elapsed_time_in_sec("Vision") / num_iters} sec'
        )
        logger.info(
            f'TensorRT-LLM LLM latency: {profiler.elapsed_time_in_sec("LLM") / num_iters} sec'
        )
        logger.info(
            f'Generate latency: {profiler.elapsed_time_in_sec("Generate") / num_iters} sec'
        )
        logger.info("---------------------------------------------------------")
