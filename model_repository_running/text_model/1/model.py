import os
import logging
import torch
import numpy as np
import tensorrt_llm
import tensorrt_llm.profiler as profiler
import triton_python_backend_utils as pb_utils
from tensorrt_llm import logger
from tensorrt_llm._utils import torch_to_numpy
from tensorrt_llm.runtime import ModelRunner, Session, TensorInfo
from transformers import pipeline, AutoTokenizer, AutoConfig
from enc_dec_model import TRTLLMEncDecModel
from trt_model_cfg import Config

logging.basicConfig(level=logging.INFO)

class TritonPythonModel:
    def initialize(self, args):
        self.config = Config()
        self.init_tokenizer()
        self.init_llm()
    
    def init_tokenizer(self):
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.hf_model_dir, use_fast=False, use_legacy=False)

        self.tokenizer.padding_side = "right"
    
    def init_llm(self):
        self.model = TRTLLMEncDecModel.from_engine(
            os.path.basename(self.config.hf_model_dir),
            self.config.llm_engine_dir,
            skip_encoder=self.config.nougat,
            debug_mode=False)

        self.model_config = self.model.encoder_model_config
        self.runtime_mapping = self.model.encoder_runtime_mapping

        config = AutoConfig.from_pretrained(self.config.hf_model_dir).text_config
        decoder_start_id = config.decoder_start_token_id
        if decoder_start_id is None:
            decoder_start_id = self.tokenizer.bos_token_id

        decoder_input_ids = torch.IntTensor([[decoder_start_id]]).to("cuda")
        batch_size = self.config.batch_size
        self.decoder_input_ids = decoder_input_ids.repeat((batch_size, 1))

    
    def setup_fake_prompts(
        self,
        visual_features,
        pre_input_ids,
        post_input_ids,
        input_lengths
    ):
        # Assemble fake prompts which points to image embedding actually
        fake_prompt_id = torch.arange(
            self.model_config.vocab_size,
            self.model_config.vocab_size +
            visual_features.shape[0] * visual_features.shape[1],
            device="cuda")
        fake_prompt_id = fake_prompt_id.reshape(visual_features.shape[0],
                                                visual_features.shape[1])

        input_ids = [fake_prompt_id, pre_input_ids]
        input_ids = torch.cat(input_ids, dim=1).contiguous().to(torch.int32).cuda()

        if self.config.decoder_llm or self.runtime_mapping.is_first_pp_rank():
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
            if not self.config.decoder_llm:
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
            if self.config.decoder_llm: tasks = tasks.unsqueeze(0)
        else:
            tasks = torch.zeros(input_ids.shape, dtype=torch.int32).cuda()

        return [prompt_table, tasks, task_vocab_size]
    
    def generate(self, visual_features, pre_prompt="", max_new_tokens=50):
        profiler.start("Generate")
        profiler.start("Vision")
        # print(visual_features)
        # print(_)
        profiler.stop("Vision")

        visual_atts = torch.ones(visual_features.size()[:-1],
                                dtype=torch.long).to("cuda")

        pre_input_ids = self.tokenizer(pre_prompt,
                                       return_tensors="pt",
                                       padding=True).input_ids.to("cuda")
        post_input_ids = None
        length = pre_input_ids.shape[1] + visual_atts.shape[1]

        input_lengths = torch.IntTensor([length] * self.config.batch_size).to(
            torch.int32).to("cuda")
        input_ids, ptuning_args = self.setup_fake_prompts(
            visual_features,
            pre_input_ids,
            post_input_ids,
            input_lengths
        )

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
            num_beams=self.config.num_beams,
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
                for batch_idx in range(self.config.batch_size)
            ]

            stripped_text = [[
                output_beams_list[batch_idx][beam_idx].strip()
                for beam_idx in range(self.config.num_beams)
            ] for batch_idx in range(self.config.batch_size)]
            profiler.stop("Generate")
            return stripped_text
        else:
            profiler.stop("Generate")
            return None

    def execute(self, requests):
        responses = []
        for request in requests:
            visual_features = pb_utils.get_input_tensor_by_name(request, "visual_features").as_numpy()
            visual_features = torch.from_numpy(visual_features)
            output_text = self.generate(visual_features)
            inference_response = pb_utils.InferenceResponse(
            output_tensors=[
                pb_utils.Tensor(
                    "text_output",
                    np.array([[o[0].encode() for o in output_text]]),
                    )
                ]
            )
            responses.append(inference_response)
        return responses

    def finalize(self):
        pass