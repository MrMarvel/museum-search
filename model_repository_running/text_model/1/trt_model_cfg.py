from dataclasses import dataclass

@dataclass
class Config:
    llm_engine_dir:str="/weights/blip2_t5/text_model_tensorrt"
    hf_model_dir:str="/weights/blip2_t5/model"
    batch_size:str=1
    nougat:bool=False
    num_beams:int=1
    decoder_llm:bool=False

