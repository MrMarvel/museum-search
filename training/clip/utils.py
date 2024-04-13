from PIL import Image
from torchvision.io import ImageReadMode, read_image

class Transforms:
    def __init__(self, image_transformations, image_column) -> None:
        self.image_transformations = image_transformations
        self.image_column = image_column
    
    def __call__(self, examples):
        images = [read_image(image_file, mode=ImageReadMode.RGB) for image_file in examples[self.image_column]]
        examples["pixel_values"] = [self.image_transformations(image) for image in images]
        return examples


def freeze_params(module):
    for param in module.parameters():
        param.requires_grad = False

def tokenize_captions(examples, tokenizer, data_args):
    captions = list(examples[data_args.caption_column])
    text_inputs = tokenizer(captions, max_length=data_args.max_seq_length, padding="max_length", truncation=True)
    examples["input_ids"] = text_inputs.input_ids
    examples["attention_mask"] = text_inputs.attention_mask
    return examples

def filter_corrupt_images(examples, image_column):
    """remove problematic images"""
    valid_images = []
    for image_file in examples[image_column]:
        try:
            Image.open(image_file)
            valid_images.append(True)
        except Exception:
            valid_images.append(False)
    return valid_images