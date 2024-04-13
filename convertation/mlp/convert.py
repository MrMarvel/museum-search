from model import MLP
import torch

if __name__ == '__main__':
    mlp = MLP()
    mlp.load_state_dict(torch.load('/weights/blip2_t5/classification/mlp.pth'))
    mlp.cuda().half()
    
    input_tensor = torch.randn((3, 1408), dtype=torch.float16).cuda()
    
    torch.onnx.export(
        mlp,
        input_tensor,
        "/weights/blip2_t5/classification/mlp.onnx",
        opset_version=17,
        input_names = ['input'],
        output_names = ['output'],
        dynamic_axes={
            'input' : {0 : 'batch_size'},
            'output' : {0 : 'batch_size'}
        }
    )
    print('Onnx success')