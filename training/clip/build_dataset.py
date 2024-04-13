import json
from collections import defaultdict

from tqdm import tqdm

if __name__ == '__main__':
    with open('datasets/test_dataset/annotations/captions_val2017.json', 'r') as f:
        data = json.load(f)
    
    id2img = {i['id']: i for i in data['images']}
    id2cap = defaultdict(list)
    [id2cap[i['image_id']].append({'id': i['id'], 'caption': i['caption']}) for i in data['annotations']]
    
    final_dataset = []
    for id, img_info in tqdm(id2img.items(), total = len(id2img)):
        while len(id2cap[id]):
            caption = id2cap[id].pop()
            final_dataset.append(
                {
                    'file_name': 'datasets/test_dataset/val2017/' + img_info['file_name'],
                    'height': img_info['height'],
                    'width': img_info['width'],
                    'img_id': img_info['id'],
                    'caption_id': caption['id'],
                    'caption': caption['caption']
                }
            )
    
    
    with open('datasets/test_dataset/annotations/captions_val2017_my.json', 'w') as f:
        json.dump({'data': final_dataset}, f)