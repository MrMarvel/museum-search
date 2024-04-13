import logging
import os
import sys
from dataclasses import dataclass, field
from typing import Optional

import torch
import transformers
from PIL import Image
from torchvision.io import ImageReadMode, read_image
from torchvision.transforms import (CenterCrop, ConvertImageDtype, Normalize,
                                    Resize)
from torchvision.transforms.functional import InterpolationMode
from transformers import (AutoImageProcessor, AutoModel, AutoTokenizer,
                          HfArgumentParser, Trainer, TrainingArguments,
                          set_seed)

from datasets import load_dataset
from utils import *

logger = logging.getLogger(__name__)


@dataclass
class ModelArguments:
    model_name: str = 'openai/clip-vit-large-patch14'
    cache_dir: str = 'weights'
    use_fast_tokenizer: bool = True
    freeze_vision_model: bool = True
    freeze_text_model: bool = False


@dataclass
class DataArguments:
    data_dir: str = 'datasets/test_dataset'
    image_column: str = 'file_name'
    caption_column: str = 'caption'
    
    train_file: Optional[str] = 'datasets/test_dataset/annotations/captions_val2017_my.json'
    validation_file: Optional[str] = None
    test_file: Optional[str] = None
    
    max_seq_length: Optional[int] = 77
    max_train_samples: Optional[int] = None
    max_eval_samples: Optional[int] = None
    
    overwrite_cache: bool = False
    preprocessing_num_workers: Optional[int] = 8


class Transform(torch.nn.Module):
    def __init__(self, image_size, mean, std):
        super().__init__()
        self.transforms = torch.nn.Sequential(
            Resize([image_size], interpolation=InterpolationMode.BICUBIC),
            CenterCrop(image_size),
            ConvertImageDtype(torch.float),
            Normalize(mean, std),
        )

    def forward(self, x) -> torch.Tensor:
        with torch.no_grad():
            x = self.transforms(x)
        return x


def data_preprocess(model_args, data_args, training_args, tokenizer, config, image_processor):
    data_files = {}
    if data_args.train_file is not None:
        data_files["train"] = data_args.train_file
        extension = data_args.train_file.split(".")[-1]
    if data_args.validation_file is not None:
        data_files["validation"] = data_args.validation_file
        extension = data_args.validation_file.split(".")[-1]
    if data_args.test_file is not None:
        data_files["test"] = data_args.test_file
        extension = data_args.test_file.split(".")[-1]
    
    dataset = load_dataset(
        extension,
        data_files=data_files,
        cache_dir=model_args.cache_dir,
        field = 'data'
    )
    
    image_transformations = Transform(
        config.vision_config.image_size,
        image_processor.image_mean,
        image_processor.image_std
    )
    image_transformations = torch.jit.script(image_transformations)
    transform_images = Transforms(image_transformations, data_args.image_column)
    
    column_names = dataset["train"].column_names
    
    datasets = {}
    for step, value in zip(['train', 'validation', 'test'], [training_args.do_train, training_args.do_eval, training_args.do_predict]):
        if value:
            step_dataset = dataset[step]
            if data_args.max_train_samples is not None:
                max_train_samples = min(len(step_dataset), data_args.max_train_samples)
                step_dataset = step_dataset.select(range(max_train_samples))

            step_dataset = step_dataset.filter(
                filter_corrupt_images,
                batched=True, 
                num_proc=data_args.preprocessing_num_workers,
                fn_kwargs={
                    'image_column': data_args.image_column
                }
            )

            step_dataset = step_dataset.map(
                function=tokenize_captions,
                batched=True,
                remove_columns=[col for col in column_names if col != data_args.image_column],
                num_proc=data_args.preprocessing_num_workers,
                load_from_cache_file=not data_args.overwrite_cache,
                desc="Running tokenizer on train dataset",
                fn_kwargs={
                    'tokenizer': tokenizer,
                    'data_args': data_args
                }
            )

            # Transform images on the fly as doing it on the whole dataset takes too much time.
            step_dataset.set_transform(transform_images)
            datasets[step] = step_dataset
    
    return datasets


def model_prepare(model_args):
    tokenizer = AutoTokenizer.from_pretrained(
        model_args.model_name,
        cache_dir=model_args.cache_dir,
        use_fast=model_args.use_fast_tokenizer
    )
 
    image_processor = AutoImageProcessor.from_pretrained(
        model_args.model_name,
        cache_dir=model_args.cache_dir
    )

    model = AutoModel.from_pretrained(
        model_args.model_name,
        cache_dir=model_args.cache_dir
    )
    
    if model_args.freeze_vision_model:
        freeze_params(model.vision_model)

    if model_args.freeze_text_model:
        freeze_params(model.text_model)
    
    return model, image_processor, tokenizer


def collate_fn(examples):
    pixel_values = torch.stack([example["pixel_values"] for example in examples])
    input_ids = torch.tensor([example["input_ids"] for example in examples], dtype=torch.long)
    attention_mask = torch.tensor([example["attention_mask"] for example in examples], dtype=torch.long)
    return {
        "pixel_values": pixel_values,
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "return_loss": True,
    }


def main():
    parser = HfArgumentParser((ModelArguments, DataArguments))
    model_args, data_args = parser.parse_args_into_dataclasses()
    
    training_args = TrainingArguments(
        'outputs',
        per_device_train_batch_size=256,
        do_train=True,
        remove_unused_columns=False
    )
    set_seed(training_args.seed)

    model, image_processor, tokenizer = model_prepare(model_args)
    datasets = data_preprocess(model_args, data_args, training_args, tokenizer, model.config, image_processor)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=datasets.get('train'),
        eval_dataset=datasets.get('eval'),
        data_collator=collate_fn,
    )

    if training_args.do_train:
        checkpoint = None
        if training_args.resume_from_checkpoint is not None:
            checkpoint = training_args.resume_from_checkpoint
        train_result = trainer.train(resume_from_checkpoint=checkpoint)
        trainer.save_model()
        tokenizer.save_pretrained(training_args.output_dir)
        image_processor.save_pretrained(training_args.output_dir)
        trainer.log_metrics("train", train_result.metrics)
        trainer.save_metrics("train", train_result.metrics)
        trainer.save_state()

    # 10. Evaluation
    if training_args.do_eval:
        metrics = trainer.evaluate()
        trainer.log_metrics("eval", metrics)
        trainer.save_metrics("eval", metrics)


if __name__ == "__main__":
    main()