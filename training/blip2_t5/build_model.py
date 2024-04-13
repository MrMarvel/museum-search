from transformers import (
    VisionTextDualEncoderProcessor,
    AutoTokenizer,
    AutoImageProcessor,
    Blip2VisionModel,
    T5EncoderModel,
)
from vision_text_dual_encoder import VisionTextDualEncoderConfig, VisionTextDualEncoderModel


if __name__ == '__main__':
    vis_enc = Blip2VisionModel.from_pretrained('weights/blip2_t5/vision_model', device_map='cuda')
    text_enc = T5EncoderModel.from_pretrained('weights/blip2_t5/text_model', device_map='cuda')
    model = VisionTextDualEncoderModel(
        VisionTextDualEncoderConfig.from_vision_text_configs(vis_enc.config, text_enc.config),
        vis_enc,
        text_enc
    )

    tokenizer = AutoTokenizer.from_pretrained("Salesforce/blip2-flan-t5-xl-coco", cache_dir='weights')
    image_processor = AutoImageProcessor.from_pretrained("Salesforce/blip2-flan-t5-xl-coco", cache_dir='weights')
    processor = VisionTextDualEncoderProcessor(image_processor, tokenizer)

    # # save the model and processor
    model.save_pretrained("weights/blip2_t5/projection")
    processor.save_pretrained("weights/blip2_t5/projection")
    
    try:
        model = VisionTextDualEncoderModel.from_pretrained(
            'weights/blip2_t5/projection',
            device_map='cuda',
            config=VisionTextDualEncoderConfig.from_pretrained('weights/blip2_t5/projection')
        )
        print('SUCCESS')
    except Exception as e:
        print(e)