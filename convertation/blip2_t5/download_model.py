from transformers import Blip2ForConditionalGeneration, Blip2Processor
import shutil

print('Downloading model to tmp dir...')
processor = Blip2Processor.from_pretrained('Salesforce/blip2-flan-t5-xl-coco', cache_dir='tmp')
model = Blip2ForConditionalGeneration.from_pretrained('Salesforce/blip2-flan-t5-xl-coco', cache_dir='tmp')
print('Downloading has been completed')

print('Saving models to /weights dir...')
model.save_pretrained('/weights/blip2_t5/model')
processor.save_pretrained('/weights/blip2_t5/model')

model.language_model.save_pretrained('/weights/blip2_t5/text_model')
model.vision_model.save_pretrained('/weights/blip2_t5/vision_model')
print('Saving has been completed')


# shutil.rmtree('tmp')
print('Tmp dir has been cleaned')